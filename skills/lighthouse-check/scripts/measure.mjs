#!/usr/bin/env node
// Run only owned, temporary Chrome profiles and persist each Lighthouse attempt.
import {createRequire} from 'node:module';
import {accessSync, constants as fsConstants, readFileSync, writeFileSync} from 'node:fs';
import {dirname, join, resolve} from 'node:path';
import {pathToFileURL} from 'node:url';

async function loadTools(folder) {
  const require = createRequire(join(resolve(folder), 'package.json'));
  const entry = require.resolve('lighthouse');
  const fromLighthouse = createRequire(entry);
  const load = specifier => import(pathToFileURL(fromLighthouse.resolve(specifier)).href);
  const lighthouse = await import(pathToFileURL(entry).href);
  const launcher = await load('chrome-launcher');
  const puppeteer = (await load('puppeteer-core')).default;
  const constants = await load('./config/constants.js');
  const version = JSON.parse(readFileSync(join(dirname(entry), '..', 'package.json'))).version;
  return {lighthouse, launcher, puppeteer, constants, version};
}

let chrome;
async function ownedChrome(tools, config, action) {
  if (config.chrome_path) accessSync(config.chrome_path, fsConstants.X_OK);
  chrome = await tools.launcher.launch({chromePath: config.chrome_path || undefined,
    chromeFlags: ['--headless'], logLevel: 'silent', handleSIGINT: false});
  try {
    return await action(chrome);
  } finally {
    await chrome.kill();
    chrome = undefined;
  }
}

async function snapshot(page, expected) {
  return page.evaluate(expectedText => {
    const visible = element => {
      const rect = element.getBoundingClientRect();
      return rect.width > 0 && rect.height > 0;
    };
    const body = document.body?.innerText || '';
    const images = [...document.images].filter(image => visible(image) && image.getBoundingClientRect().top < innerHeight);
    return {
      title: document.title,
      heading: document.querySelector('h1')?.textContent?.slice(0, 300) || '',
      text_sample: body.slice(0, 1500), has_text: body.trim().length > 0,
      has_visual: [...document.querySelectorAll('img,canvas,svg,video')].some(visible),
      password_form: [...document.querySelectorAll('input[type="password"]')].some(visible),
      expected_text_found: !expectedText || body.includes(expectedText),
      broken_visible_images: images.filter(image => !image.naturalWidth).map(image => image.currentSrc).slice(0, 10),
    };
  }, expected || '');
}

function scenarioProblems(data, requested, final) {
  const problems = [];
  if (!data.has_text && !data.has_visual) problems.push('No visible page content');
  if (!data.expected_text_found) problems.push('Expected page text is absent');
  if (data.password_form) problems.push('Visible password form; anonymous scenario needs confirmation');
  if (/captcha|just a moment|access denied|verify you are human|application error|internal server error/i.test(`${data.title} ${data.heading}`)) {
    problems.push('Possible access challenge or application error screen');
  }
  if (new URL(final).pathname !== new URL(requested).pathname && /\/(login|signin|sign-in|auth)(\/|$)/i.test(new URL(final).pathname)) {
    problems.push('Navigation redirected to authentication');
  }
  return problems;
}

async function smoke(tools, config, state) {
  return ownedChrome(tools, config, async instance => {
    const browser = await tools.puppeteer.connect({browserURL: `http://127.0.0.1:${instance.port}`, defaultViewport: null});
    try {
      state.chrome_version = await browser.version();
      const page = await browser.newPage();
      const errors = [];
      page.on('pageerror', error => { if (errors.length < 30) errors.push(String(error)); });
      page.on('console', message => { if (message.type() === 'error' && errors.length < 30) errors.push(message.text()); });
      const viewport = tools.constants.screenEmulationMetrics[config.device];
      await page.setViewport({width: viewport.width, height: viewport.height,
        deviceScaleFactor: viewport.deviceScaleFactor, isMobile: viewport.mobile});
      await page.setUserAgent({userAgent: tools.constants.userAgents[config.device]});
      const response = await page.goto(config.url, {waitUntil: 'domcontentloaded', timeout: 30000});
      let networkIdle = true;
      await page.waitForNetworkIdle({idleTime: 500, timeout: 5000}).catch(() => { networkIdle = false; });
      const data = await snapshot(page, config.expected_text);
      const final = page.url();
      const problems = scenarioProblems(data, config.url, final);
      if (!response || response.status() >= 400) problems.push(`Document HTTP status: ${response?.status()}`);
      await page.screenshot({path: join(config.output_dir, 'browser.png')});
      return {...data, final_url: final, status: response?.status(), viewport,
        ready: !problems.length, problems, console_errors: errors, network_idle: networkIdle,
        consent_state: 'Fresh anonymous profile; no consent interaction', screenshot: 'browser.png'};
    } finally {
      await browser.disconnect();
    }
  });
}

async function main(config) {
  const target = join(config.output_dir, 'measurement.json');
  const state = {status: 'INCOMPLETE', files: [], invalid_files: [], errors: [], node_version: process.version};
  const save = () => writeFileSync(target, JSON.stringify(state, null, 2) + '\n');
  const interrupted = async signal => {
    state.errors.push(`Measurement interrupted: ${signal}`);
    save();
    if (chrome) await chrome.kill().catch(() => {});
    process.exit(2);
  };
  process.once('SIGTERM', () => void interrupted('SIGTERM'));
  process.once('SIGINT', () => void interrupted('SIGINT'));
  save();
  try {
    const tools = await loadTools(config.tools_dir);
    state.lighthouse_version = tools.version;
    console.error('Checking anonymous browser scenario');
    state.browser = await smoke(tools, config, state);
    save();
    if (!state.browser.ready) throw new Error(state.browser.problems.join('; '));
    for (let index = 1; index <= config.runs; index++) {
      console.error(`Lighthouse ${index}/${config.runs}: ${config.device}`);
      const filename = `lighthouse-${index}.json`;
      await ownedChrome(tools, config, async instance => {
        const browser = await tools.puppeteer.connect({browserURL: `http://127.0.0.1:${instance.port}`, defaultViewport: null});
        try {
          const page = await browser.newPage();
          const flags = {port: instance.port, logLevel: 'error', output: 'json', locale: config.language,
            onlyCategories: ['performance', 'accessibility', 'best-practices', 'seo'], maxWaitForLoad: 45000};
          const result = await tools.lighthouse.default(config.url, flags,
            config.device === 'desktop' ? tools.lighthouse.desktopConfig : undefined, page);
          if (!result?.lhr) throw new Error('Lighthouse returned no report');
          writeFileSync(join(config.output_dir, filename), JSON.stringify(result.lhr) + '\n');
          state.files.push(filename);
          state.invalid_files.push(filename);
          save();
          if (result.lhr.runtimeError) throw new Error(JSON.stringify(result.lhr.runtimeError));
          const data = await snapshot(page, config.expected_text);
          const problems = scenarioProblems(data, config.url, result.lhr.finalDisplayedUrl);
          if (result.lhr.finalDisplayedUrl !== state.browser.final_url) problems.push('Measured URL differs from the browser check');
          if (problems.length) {
            throw new Error(problems.join('; '));
          }
          state.invalid_files = state.invalid_files.filter(item => item !== filename);
        } finally {
          await browser.disconnect();
        }
      });
      save();
    }
    state.status = 'COMPLETED';
  } catch (error) {
    state.errors.push(String(error.message || error));
    process.exitCode = 2;
  } finally {
    save();
  }
}

try {
  if (process.argv[2] === '--check-tools') {
    const tools = await loadTools(process.argv[3]);
    console.log(JSON.stringify({lighthouse_version: tools.version, node_version: process.version}));
  } else {
    await main(JSON.parse(readFileSync(process.argv[2], 'utf8')));
  }
} catch (error) {
  console.error(String(error.message || error));
  process.exitCode = 2;
}

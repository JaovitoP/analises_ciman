import { browser } from 'k6/browser';
import { check } from 'k6';

const baseUrl = (__ENV.BASE_URL || 'http://localhost:8501').replace(/\/$/, '');
const requestedPage = (__ENV.TEST_PAGE || 'all').toLowerCase();
const pages = ['Brasil', 'Biomas', 'Estados', 'Regiões'];

export const options = {
  scenarios: {
    streamlit_browser: {
      executor: 'ramping-vus',
      startVUs: 1,
      stages: [
        { target: Number(__ENV.TEST_VUS || 10), duration: __ENV.TEST_RAMP_UP || '2m' },
        { target: Number(__ENV.TEST_VUS || 10), duration: __ENV.TEST_HOLD || '5m' },
        { target: 0, duration: __ENV.TEST_RAMP_DOWN || '1m' },
      ],
      options: {
        browser: {
          type: 'chromium',
        },
      },
    },
  },
  thresholds: {
    checks: ['rate>0.95'],
    browser_web_vital_fcp: ['p(95)<10000'],
  },
  summaryTrendStats: ['avg', 'min', 'med', 'p(90)', 'p(95)', 'max'],
};

function pageForVu() {
  if (requestedPage !== 'all') {
    return pages.find((page) => page.toLowerCase() === requestedPage) || 'Brasil';
  }
  return pages[(__VU - 1) % pages.length];
}

async function openPage(page, name) {
  await page.goto(`${baseUrl}/`, { waitUntil: 'domcontentloaded', timeout: 60000 });
  await page.waitForTimeout(2500);

  if (name !== 'Brasil') {
    const navigationItem = page.getByText(name, { exact: true });
    await navigationItem.click({ timeout: 30000 });
    await page.waitForTimeout(2500);
  }

  // The application generates the report automatically after the page rerun.
  const report = page.getByText(/Analisador de focos/).first();
  await report.waitFor({ state: 'visible', timeout: 30000 });
  return true;
}

async function exerciseFilters(page) {
  if ((__ENV.TEST_INTERACTIONS || '0') !== '1') {
    return true;
  }

  const comboboxes = page.locator('[role="combobox"]');
  const count = await comboboxes.count();
  if (count < 2) {
    return false;
  }

  // Changing a year forces another Streamlit rerun without depending on a
  // specific dataset value being available in the current year.
  await comboboxes.nth(0).click();
  await page.waitForTimeout(250);
  const options = page.locator('[role="option"]');
  if (await options.count() > 1) {
    await options.nth(1).click();
  }
  await page.waitForTimeout(1500);
  return true;
}

export default async function () {
  const page = await browser.newPage();
  let loaded = false;
  let filters = true;

  try {
    loaded = await openPage(page, pageForVu());
    filters = await exerciseFilters(page);
  } finally {
    await page.close();
  }

  check(null, {
    'report page loaded': () => loaded,
    'optional filter interaction completed': () => filters,
  });
}

export function handleSummary(data) {
  const resultDirectory = __ENV.TEST_RESULTS_DIR || '/results';
  const summary = JSON.stringify({
    test: {
      base_url: baseUrl,
      page: requestedPage,
      interactions: (__ENV.TEST_INTERACTIONS || '0') === '1',
      configured_vus: Number(__ENV.TEST_VUS || 10),
      ramp_up: __ENV.TEST_RAMP_UP || '2m',
      hold: __ENV.TEST_HOLD || '5m',
      ramp_down: __ENV.TEST_RAMP_DOWN || '1m',
    },
    k6: data,
  }, null, 2);

  return {
    stdout: summary,
    [`${resultDirectory}/k6-summary.json`]: summary,
  };
}

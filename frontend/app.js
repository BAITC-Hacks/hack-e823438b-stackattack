"use strict";

const form = document.querySelector('#event-form');
const searchButton = form.querySelector('.search-button');
const note = document.querySelector('#preview-note');
const retry = document.querySelector('#retry-catalogue');
const status = document.querySelector('#search-status');
const results = document.querySelector('#search-results');
const panel = document.querySelector('.results-panel');
const emptyState = document.querySelector('.empty-state');
const money = new Intl.NumberFormat('ru-KZ', { maximumFractionDigits: 2 });
let ready = false;
let pending = false;
let lastQuery = null;

function element(tag, text, className) {
  const node = document.createElement(tag);
  if (text !== undefined) node.textContent = text;
  if (className) node.className = className;
  return node;
}

async function api(path, body) {
  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), 15000);
  try {
    const response = await fetch(path, {
      signal: controller.signal,
      ...(body ? { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body) } : {})
    });
    const data = await response.json();
    if (!response.ok) {
      const message = typeof data.detail === 'string' ? data.detail :
        response.status === 422 ? 'Проверьте дату, бюджет и остальные параметры формы.' : 'Не удалось выполнить запрос. Попробуйте ещё раз.';
      throw new Error(message);
    }
    return data;
  } catch (error) {
    if (error.name === 'AbortError') throw new Error('Сервер не ответил за 15 секунд. Повторите поиск.');
    if (error instanceof TypeError || error instanceof SyntaxError) throw new Error('Не удалось связаться с API. Откройте сайт через http://127.0.0.1:8000 и проверьте, запущен ли сервер.');
    throw error;
  } finally {
    clearTimeout(timeout);
  }
}

async function loadCatalogue() {
  ready = false;
  searchButton.disabled = true;
  retry.hidden = true;
  note.textContent = 'Загружаем варианты из каталога…';
  try {
    if (location.protocol === 'file:') throw new Error('Откройте сайт через http://127.0.0.1:8000 после запуска сервера.');
    const data = await api('/api/filters');
    for (const [id, key] of [['city', 'cities'], ['category', 'categories'], ['event-format', 'event_formats'], ['language', 'languages']]) {
      const select = document.getElementById(id);
      const placeholder = select.options[0].cloneNode(true);
      select.replaceChildren(placeholder);
      for (const value of data[key]) select.add(new Option(value, value));
      select.value = '';
    }
    ready = true;
    searchButton.disabled = false;
    note.textContent = 'Подбор по данным каталога. Цена «от» и доступность требуют подтверждения у подрядчика.';
  } catch (error) {
    note.textContent = error.message;
    retry.hidden = false;
  }
}

function readQuery() {
  const values = new FormData(form);
  return {
    city: values.get('city'), date: values.get('date'),
    event_format: values.get('event_format'), category: values.get('category'),
    budget: Number(values.get('budget')),
    duration_hours: values.get('duration_hours') ? Number(values.get('duration_hours')) : null,
    language: values.get('language') || null
  };
}

function disclosure(title) {
  const details = element('details', undefined, 'result-details');
  details.append(element('summary', title));
  return details;
}

function renderCard(card, index) {
  const article = element('article', undefined, 'contractor-card');
  const heading = element('div', undefined, 'contractor-heading');
  heading.append(element('span', String(index + 1).padStart(2, '0'), 'step-number'), element('h3', card.name));
  article.append(heading, element('p', `от ${money.format(Number(card.price))} ₸`, 'contractor-price'));
  article.append(element('p', `${card.city} · ${card.categories.join(', ')}`, 'contractor-meta'));
  article.append(element('p', `Индекс запаса бюджета: ${money.format(Number(card.score) * 100)} / 100`, 'score-label'));
  const details = disclosure('WHY THIS · Почему выбран');
  const list = element('ul');
  card.why_this.forEach(reason => list.append(element('li', reason.text)));
  details.append(list, element('p', 'Индекс = (бюджет − стартовая цена) / бюджет. При нулевом бюджете — 0. При равенстве сортируем по ID. Это не оценка качества услуг.', 'field-hint'));
  const confidence = card.data_confidence;
  const origin = value => value === true ? 'дополнено' : value === false ? 'исходное' : 'неизвестно';
  details.append(element('p', `Город: ${origin(confidence.city_imputed)} · Цена: ${origin(confidence.price_imputed)} · Профиль: ${confidence.synthetic === true ? 'синтетический' : confidence.synthetic === false ? 'не синтетический' : 'происхождение неизвестно'}`, 'provenance'));
  article.append(details);
  return article;
}

function renderRejections(data) {
  const details = disclosure(`WHY NOT · Почему не остальные (${data.rejections.length})`);
  if (!data.rejections.length) details.append(element('p', 'Все профили каталога попали в результат.'));
  const display = value => value === null ? 'не указано' : Array.isArray(value) ? value.join(', ') || 'не указано' : String(value);
  for (const [code, group] of Object.entries(data.why_not)) {
    const section = disclosure(`${group.label} · ${group.count}`);
    const list = element('ul', undefined, 'rejection-list');
    for (const rejection of data.rejections.filter(item => item.reason === code)) {
      const item = element('li');
      item.append(element('strong', `${rejection.name} · ${rejection.contractor_id}`));
      let explanation;
      if (code === 'below_top_3') explanation = `Место ${rejection.rank}; индекс запаса бюджета ${money.format(Number(rejection.score) * 100)} / 100.`;
      else if (code === 'busy') explanation = `Дата ${rejection.requested} указана среди занятых.`;
      else explanation = `Условие: ${display(rejection.requested)}. В каталоге: ${display(rejection.actual)}.`;
      item.append(element('p', explanation));
      list.append(item);
    }
    section.append(list);
    details.append(section);
  }
  return details;
}

function render(data) {
  results.replaceChildren();
  const query = data.query;
  const date = new Intl.DateTimeFormat('ru', { day: 'numeric', month: 'long', year: 'numeric' }).format(new Date(`${query.date}T12:00:00`));
  const dna = [query.city, query.event_format, date, query.category, `до ${money.format(Number(query.budget))} ₸`];
  if (query.duration_hours !== null) dna.push(`${query.duration_hours} ч`);
  if (query.language) dna.push(query.language);
  results.append(element('p', dna.join(' · '), 'query-dna'));
  const funnel = element('ol', undefined, 'funnel');
  const stages = [['total', 'Всего'], ['category', 'Категория'], ['city', 'Город'], ['event_format', 'Формат'], ['availability', 'Дата'], ['budget', 'Бюджет']];
  if (query.duration_hours !== null) stages.push(['duration', 'Часы']);
  if (query.language) stages.push(['language', 'Язык']);
  stages.push(['final', 'Подходят']);
  for (const [key, title] of stages) {
    const item = element('li');
    item.append(element('strong', String(data.funnel[key])), element('span', title));
    funnel.append(item);
  }
  results.append(funnel);
  if (!data.recommendations.length) {
    const message = element('div', undefined, 'no-results');
    message.append(element('h3', 'Подходящих подрядчиков пока нет'), element('p', 'Посмотрите причины ниже и попробуйте другую дату, бюджет или длительность.'));
    results.append(message);
  } else {
    results.append(element('p', `Подходят: ${data.eligible_count} · Показаны: ${data.returned_count}`, 'result-count'));
    data.recommendations.forEach((card, index) => results.append(renderCard(card, index)));
  }
  results.append(renderRejections(data));
  emptyState.hidden = true;
  results.hidden = false;
}

form.addEventListener('submit', async event => {
  event.preventDefault();
  if (!ready || pending || !form.reportValidity()) return;
  const query = readQuery();
  pending = true;
  searchButton.disabled = true;
  searchButton.textContent = 'Подбираем…';
  panel.setAttribute('aria-busy', 'true');
  results.hidden = true;
  emptyState.hidden = true;
  lastQuery = null;
  status.textContent = 'Проверяем условия и занятые даты…';
  try {
    const data = await api('/api/recommend', query);
    render(data);
    lastQuery = JSON.stringify(query);
    status.textContent = `Поиск завершён. Показано: ${data.returned_count}.`;
    if (JSON.stringify(readQuery()) !== lastQuery) status.textContent += ' Параметры формы изменились — выполните поиск снова.';
  } catch (error) {
    status.textContent = error.message;
  } finally {
    pending = false;
    searchButton.disabled = !ready;
    searchButton.textContent = 'Найти моих подрядчиков ↗';
    panel.setAttribute('aria-busy', 'false');
  }
});
form.addEventListener('input', () => {
  if (lastQuery && !pending) status.textContent = JSON.stringify(readQuery()) === lastQuery ? 'Результаты соответствуют параметрам формы.' : 'Параметры изменились. Нажмите «Найти», чтобы обновить результаты.';
});
retry.addEventListener('click', loadCatalogue);
loadCatalogue();

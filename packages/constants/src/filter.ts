/**
 * Copyright (c) 2023-present Plane Software, Inc. and contributors
 * SPDX-License-Identifier: AGPL-3.0-only
 * See the LICENSE file for details.
 */

export enum E_SORT_ORDER {
  ASC = "asc",
  DESC = "desc",
}
// EWH: presets relativos resolvidos no backend a cada consulta —
// uma View salva com "Hoje" continua correta amanhã, sem edição.
export const DATE_AFTER_FILTER_OPTIONS = [
  {
    name: "Hoje",
    value: "today;exact;fromnow",
  },
  {
    name: "Amanhã",
    value: "tomorrow;exact;fromnow",
  },
  {
    name: "Ontem",
    value: "yesterday;exact;fromnow",
  },
  {
    name: "Atrasadas (antes de hoje)",
    value: "yesterday;before;fromnow",
  },
  {
    name: "Esta semana",
    value: "this_week;exact;fromnow",
  },
  {
    name: "Próxima semana",
    value: "next_week;exact;fromnow",
  },
  {
    name: "Este mês",
    value: "this_month;exact;fromnow",
  },
  {
    name: "Próximos 7 dias",
    value: "7_days;next;fromnow",
  },
  {
    name: "Próximos 30 dias",
    value: "30_days;next;fromnow",
  },
  {
    name: "Últimos 7 dias",
    value: "7_days;last;fromnow",
  },
  {
    name: "A partir de amanhã",
    value: "tomorrow;after;fromnow",
  },
  {
    name: "Sem data",
    value: "no_date;exact;fromnow",
  },
  {
    name: "Daqui a 1 semana",
    value: "1_weeks;after;fromnow",
  },
  {
    name: "Daqui a 1 mês",
    value: "1_months;after;fromnow",
  },
];

export const DATE_BEFORE_FILTER_OPTIONS = [
  {
    name: "1 week ago",
    value: "1_weeks;before;fromnow",
  },
  {
    name: "2 weeks ago",
    value: "2_weeks;before;fromnow",
  },
  {
    name: "1 month ago",
    i18n_name: "date_filters.1_month_ago",
    value: "1_months;before;fromnow",
  },
];

export const PROJECT_CREATED_AT_FILTER_OPTIONS = [
  {
    name: "Today",
    value: "today;custom;custom",
  },
  {
    name: "Yesterday",
    value: "yesterday;custom;custom",
  },
  {
    name: "Last 7 days",
    value: "last_7_days;custom;custom",
  },
  {
    name: "Last 30 days",
    value: "last_30_days;custom;custom",
  },
];

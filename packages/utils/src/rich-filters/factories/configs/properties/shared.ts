/**
 * Copyright (c) 2023-present Plane Software, Inc. and contributors
 * SPDX-License-Identifier: AGPL-3.0-only
 * See the LICENSE file for details.
 */

// plane imports
import type { IProject, IUserLite, TOperatorConfigMap, TSupportedOperators } from "@plane/types";
import { COMPARISON_OPERATOR, EQUALITY_OPERATOR } from "@plane/types";
// local imports
import { getDateRangePickerConfig, getMultiSelectConfig, getSingleSelectConfig } from "../core";
import type { IFilterIconConfig, TCreateDateFilterParams, TCreateFilterConfigParams, TFilterIconType } from "../shared";
import { createOperatorConfigEntry } from "../shared";

// ------------ Base User Filter Types ------------

/**
 * User filter specific params
 */
export type TCreateUserFilterParams = TCreateFilterConfigParams &
  IFilterIconConfig<IUserLite> & {
    members: IUserLite[];
  };

/**
 * Helper to get the member multi select config
 * @param params - The filter params
 * @returns The member multi select config
 */
export const getMemberMultiSelectConfig = (params: TCreateUserFilterParams, singleValueOperator: TSupportedOperators) =>
  getMultiSelectConfig<IUserLite, string, IUserLite>(
    {
      items: params.members,
      getId: (member) => member.id,
      getLabel: (member) => member.display_name,
      getValue: (member) => member.id,
      getIconData: (member) => member,
    },
    {
      singleValueOperator,
      ...params,
    },
    {
      ...params,
    }
  );

// ------------ Date Operators ------------

// EWH: períodos relativos oferecidos no operador "é" dos filtros de data.
// O valor é um token resolvido pelo BACKEND a cada consulta (issue_filters/
// filterset) — por isso uma View salva com "Hoje" continua correta amanhã.
// Datas absolutas continuam disponíveis pelo operador de intervalo (RANGE).
type TEwhRelativeDatePreset = { label: string; value: string };
export const EWH_RELATIVE_DATE_PRESETS: TEwhRelativeDatePreset[] = [
  { label: "Hoje", value: "today;exact;fromnow" },
  { label: "Amanhã", value: "tomorrow;exact;fromnow" },
  { label: "Ontem", value: "yesterday;exact;fromnow" },
  { label: "Atrasadas (antes de hoje)", value: "yesterday;before;fromnow" },
  { label: "Esta semana", value: "this_week;exact;fromnow" },
  { label: "Próxima semana", value: "next_week;exact;fromnow" },
  { label: "Este mês", value: "this_month;exact;fromnow" },
  { label: "Próximos 7 dias", value: "7_days;next;fromnow" },
  { label: "Próximos 30 dias", value: "30_days;next;fromnow" },
  { label: "Últimos 7 dias", value: "7_days;last;fromnow" },
  { label: "A partir de amanhã", value: "tomorrow;after;fromnow" },
  { label: "Sem data", value: "no_date;exact;fromnow" },
];

export const getSupportedDateOperators = (params: TCreateDateFilterParams): TOperatorConfigMap =>
  new Map([
    createOperatorConfigEntry(EQUALITY_OPERATOR.EXACT, params, (updatedParams) =>
      getSingleSelectConfig<TEwhRelativeDatePreset, string, undefined>(
        {
          items: EWH_RELATIVE_DATE_PRESETS,
          getId: (option) => option.value,
          getLabel: (option) => option.label,
          getValue: (option) => option.value,
        },
        { ...updatedParams }
      )
    ),
    createOperatorConfigEntry(COMPARISON_OPERATOR.RANGE, params, (updatedParams) =>
      getDateRangePickerConfig(updatedParams)
    ),
  ]);

// ------------ Project filter ------------

/**
 * Project filter specific params
 */
export type TCreateProjectFilterParams = TCreateFilterConfigParams &
  IFilterIconConfig<IProject> & {
    projects: IProject[];
  };

/**
 * Helper to get the project multi select config
 * @param params - The filter params
 * @returns The member multi select config
 */
export const getProjectMultiSelectConfig = (
  params: TCreateProjectFilterParams,
  singleValueOperator: TSupportedOperators
) =>
  getMultiSelectConfig<IProject, string, IProject>(
    {
      items: params.projects,
      getId: (project) => project.id,
      getLabel: (project) => project.name,
      getValue: (project) => project.id,
      getIconData: (project) => project,
    },
    {
      singleValueOperator,
      ...params,
    },
    {
      ...params,
    }
  );

/**
 * Custom property filter specific params
 */
export type TCustomPropertyFilterParams<T extends TFilterIconType> = TCreateFilterConfigParams &
  IFilterIconConfig<T> & {
    propertyDisplayName: string;
  };

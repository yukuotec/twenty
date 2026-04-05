import { Injectable } from '@nestjs/common';

import {
  ALL_METADATA_NAME,
  type AllMetadataName,
} from 'twenty-shared/metadata';
import { type APP_LOCALES, SOURCE_LOCALE } from 'twenty-shared/translations';
import { ViewVisibility } from 'twenty-shared/types';
import { isDefined, uncapitalize } from 'twenty-shared/utils';
import { isNonEmptyString } from '@sniptt/guards';

import { ALL_FLAT_ENTITY_MAPS_PROPERTIES } from 'src/engine/metadata-modules/flat-entity/constant/all-flat-entity-maps-properties.constant';
import { WorkspaceManyOrAllFlatEntityMapsCacheService } from 'src/engine/metadata-modules/flat-entity/services/workspace-many-or-all-flat-entity-maps-cache.service';
import { I18nService } from 'src/engine/core-modules/i18n/i18n.service';
import { type CollectionHashDTO } from 'src/engine/metadata-modules/minimal-metadata/dtos/collection-hash.dto';
import { MinimalMetadataDTO } from 'src/engine/metadata-modules/minimal-metadata/dtos/minimal-metadata.dto';
import { MinimalObjectMetadataDTO } from 'src/engine/metadata-modules/minimal-metadata/dtos/minimal-object-metadata.dto';
import { MinimalViewDTO } from 'src/engine/metadata-modules/minimal-metadata/dtos/minimal-view.dto';
import { generateMessageId } from 'src/engine/core-modules/i18n/utils/generateMessageId';
import { WorkspaceCacheService } from 'src/engine/workspace-cache/services/workspace-cache.service';
import { type WorkspaceCacheKeyName } from 'src/engine/workspace-cache/types/workspace-cache-key.type';

const flatMapsKeyToMetadataName = (
  flatMapsKey: string,
): AllMetadataName | undefined => {
  const withoutPrefix = flatMapsKey.replace(/^flat/, '');
  const withoutSuffix = withoutPrefix.replace(/Maps$/, '');
  const metadataName = uncapitalize(withoutSuffix);

  return metadataName in ALL_METADATA_NAME
    ? (metadataName as AllMetadataName)
    : undefined;
};

@Injectable()
export class MinimalMetadataService {
  constructor(
    private readonly flatEntityMapsCacheService: WorkspaceManyOrAllFlatEntityMapsCacheService,
    private readonly workspaceCacheService: WorkspaceCacheService,
    private readonly i18nService: I18nService,
  ) {}

  private translateLabel(
    label: string | null | undefined,
    locale: keyof typeof APP_LOCALES | undefined,
  ): string {
    if (!isNonEmptyString(label)) {
      return '';
    }

    const safeLocale = locale ?? SOURCE_LOCALE;

    // Only translate for non-source locales
    if (safeLocale === SOURCE_LOCALE) {
      return label;
    }

    const i18nInstance = this.i18nService.getI18nInstance(safeLocale);

    if (!i18nInstance) {
      return label;
    }

    const messageId = generateMessageId(label);
    const translatedMessage = i18nInstance._(messageId);

    // If translation not found, return original label
    if (translatedMessage === messageId) {
      return label;
    }

    return translatedMessage;
  }

  async getMinimalMetadata(
    workspaceId: string,
    userWorkspaceId?: string,
    locale?: string,
  ): Promise<MinimalMetadataDTO> {
    const [{ flatObjectMetadataMaps, flatViewMaps }, cacheHashes] =
      await Promise.all([
        this.flatEntityMapsCacheService.getOrRecomputeManyOrAllFlatEntityMaps({
          workspaceId,
          flatMapsKeys: ['flatObjectMetadataMaps', 'flatViewMaps'],
        }),
        this.workspaceCacheService.getCacheHashes(
          workspaceId,
          ALL_FLAT_ENTITY_MAPS_PROPERTIES as WorkspaceCacheKeyName[],
        ),
      ]);

    const collectionHashes: CollectionHashDTO[] = Object.entries(cacheHashes)
      .map(([cacheKey, hash]) => {
        const metadataName = flatMapsKeyToMetadataName(cacheKey);

        if (!isDefined(metadataName) || !isDefined(hash)) {
          return undefined;
        }

        return { collectionName: metadataName, hash };
      })
      .filter(isDefined);

    const objectMetadataItems: MinimalObjectMetadataDTO[] = Object.values(
      flatObjectMetadataMaps.byUniversalIdentifier,
    )
      .filter(isDefined)
      .filter((flatObjectMetadata) => flatObjectMetadata.isActive === true)
      .map((flatObjectMetadata) => {
        // Translate labels for standard objects (non-custom)
        const isCustom = flatObjectMetadata.isCustom;
        const labelSingular = isCustom
          ? (flatObjectMetadata.labelSingular ?? '')
          : this.translateLabel(
              flatObjectMetadata.labelSingular,
              locale as keyof typeof APP_LOCALES | undefined,
            );
        const labelPlural = isCustom
          ? (flatObjectMetadata.labelPlural ?? '')
          : this.translateLabel(
              flatObjectMetadata.labelPlural,
              locale as keyof typeof APP_LOCALES | undefined,
            );

        return {
          id: flatObjectMetadata.id,
          nameSingular: flatObjectMetadata.nameSingular,
          namePlural: flatObjectMetadata.namePlural,
          labelSingular,
          labelPlural,
          icon: flatObjectMetadata.icon ?? undefined,
          isCustom: flatObjectMetadata.isCustom,
          isActive: flatObjectMetadata.isActive,
          isSystem: flatObjectMetadata.isSystem,
          isRemote: flatObjectMetadata.isRemote,
        };
      });

    const views: MinimalViewDTO[] = Object.values(
      flatViewMaps.byUniversalIdentifier,
    )
      .filter(isDefined)
      .filter((flatView) => flatView.workspaceId === workspaceId)
      .filter((flatView) => flatView.deletedAt === null)
      .filter(
        (flatView) =>
          flatView.visibility === ViewVisibility.WORKSPACE ||
          (flatView.visibility === ViewVisibility.UNLISTED &&
            isDefined(userWorkspaceId) &&
            flatView.createdByUserWorkspaceId === userWorkspaceId),
      )
      .map((flatView) => ({
        id: flatView.id,
        type: flatView.type,
        key: flatView.key,
        objectMetadataId: flatView.objectMetadataId,
      }));

    return {
      objectMetadataItems,
      views,
      collectionHashes,
    };
  }
}

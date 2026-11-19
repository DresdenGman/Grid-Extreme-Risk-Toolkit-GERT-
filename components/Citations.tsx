import { CI_ARCHIVE_NOTE, DATASET_DOI, DATASET_PUBLISHED, DATASET_VERSION, doiUrl, PRODUCT_NAME, SOFTWARE_CONCEPT_DOI, SOFTWARE_PUBLISHED, SOFTWARE_VERSION } from '@/lib/citations';

export function Citations() {
  return (
    <footer className="mt-12 border-t border-black/15 pt-6 text-xs leading-5 text-[#514e48]">
      <p className="font-semibold text-[#141414]">{PRODUCT_NAME}</p>
      <p className="mt-2 max-w-3xl">
        Software concept DOI{' '}
        <a className="underline" href={doiUrl(SOFTWARE_CONCEPT_DOI)}>{SOFTWARE_CONCEPT_DOI}</a>
        {' '}({SOFTWARE_VERSION}, published {SOFTWARE_PUBLISHED}).
        Dataset DOI{' '}
        <a className="underline" href={doiUrl(DATASET_DOI)}>{DATASET_DOI}</a>
        {' '}({DATASET_VERSION}, published {DATASET_PUBLISHED}).
      </p>
      <p className="mt-2 max-w-3xl" data-testid="test-count-citation">
        {CI_ARCHIVE_NOTE}
      </p>
    </footer>
  );
}

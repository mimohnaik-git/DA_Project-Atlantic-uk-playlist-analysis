# Nationality Classification Methodology

The analysis uses three categories: `UK / Domestic`, `International` and `Unclassified`.

Classification is based on the primary billed artist or act's country of origin. A group's classification follows the billed group's origin rather than assigning separate nationalities to members. Multinational acts, soundtrack or media credits, novelty names and artists whose origin cannot be supported confidently remain `Unclassified`.

The current mapping in `src/artist_nationality.py` was manually curated in the existing project. The repository contains no structured source references for the individual classifications. The remediation therefore preserves the useful classification concept and the explicit Unclassified category, but does not invent citations. Before external publication, review each mapped artist against an authoritative biography or official artist source and record the source URL, access date and classification rationale in a structured mapping file.

Two weighting methods are reported:

- Full artist-credit share gives every credited artist one full observation.
- Fractional chart-entry share divides each chart entry equally among its credited artists so every entry contributes total weight one.

The unclassified rate is always reported and Unclassified values are not redistributed between UK and International.

# Metric Methodology

This note documents the calculation and interpretation of the headline measures used in the UK Top 50 portfolio analysis.

## Analytical grains

- **Chart entry:** one playlist position observed in one reconstructed Top-50 snapshot.
- **Artist credit:** one credited artist attached to a chart entry. Collaborations create multiple artist-credit rows.
- **Recording proxy:** a dataset-local recording identity based on normalized title plus exact duration. It is not an ISRC or global recording identifier.
- **Snapshot:** one reconstructed 50-position chart state.

### Canonical recording-proxy metadata

The recording proxy identity is normalized title + exact `duration_ms`. When a proxy appears repeatedly with changing metadata, the canonical recording table keeps the earliest observed row after sorting by `date` and `source_row_id`. This deterministic **first-observed** rule is used for proxy-level attributes, including the 15.61% recording-proxy collaboration share. It is a reproducibility convention, not a claim that the first-observed artist set or metadata is the globally correct recording metadata.

## Artist concentration

### Period-wide HHI

`HHI = 10,000 × Σ(pᵢ²)`

`pᵢ` is an artist's share of full artist-credit appearances across the selected period. This measures long-run appearance concentration or persistence. It is not the same as concentration within a typical Top-50 snapshot.

### Snapshot HHI

For each chart entry, credited artists divide a total fractional weight of 1 equally. Artist shares are then calculated within each reconstructed snapshot and HHI is computed from those fractional shares.

The dashboard reports median and mean snapshot HHI separately from period-wide HHI.

## Artist diversity

### Shannon diversity

`H = -Σ(pᵢ × ln pᵢ)`

`pᵢ` is the fractional artist share within one reconstructed snapshot.

### Effective artist count

`Effective artists = exp(H)`

This converts entropy into an intuitive equivalent number of equally represented artists. Effective artist count is calculated separately for every snapshot and then summarized across snapshots.

### Unique artists

The dashboard also reports the number of distinct credited artists in each snapshot. This is a direct count and should be interpreted separately from entropy-based diversity.

## Collaboration

Collaboration is reported at more than one grain:

- **Chart-entry collaboration share:** share of repeated chart observations credited to more than one artist.
- **Recording-proxy collaboration share:** share of dataset-local recording proxies credited to more than one artist.
- **Pair appearances:** repeated chart appearances for a credited artist pair.
- **Pair recording proxies:** distinct collaborative recording proxies associated with that pair.

Repeated chart persistence is therefore not treated as additional unique collaborative catalogue.

## Nationality classification

Nationality is manually curated from the billed act's primary origin. Groups are classified at the billed-act level rather than by individual member origins. Multinational or uncertain acts remain **Unclassified**.

The analysis distinguishes full artist-credit weighting from fractional-entry weighting. Individual nationality mappings should be source-reviewed before external publication because the supplied project materials do not provide structured citations for each mapping.

## Retired legacy measures

The earlier **Diversity Score** and custom **Content Variety Index** are not used as headline measures in the final dashboard.

- The Diversity Score was sensitive to the length of the observation window.
- The Content Variety Index combined artist variety, release-format mix, and explicit/clean balance into a custom weighted composite.

The final analysis instead uses snapshot-level unique artists, Shannon diversity, effective artist count, and HHI. The legacy helper functions were removed from the active analytics layer; the historical definitions remain documented only for evaluation traceability.

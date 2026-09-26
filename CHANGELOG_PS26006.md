# Update — PS-26006 Vessel & Trade-Lane Revision

## Implemented

1. Removed user-selected Vessel Class and Vessel Subtype from the main dashboard.
2. Added Cargo Material selector: Coal / Steel.
3. Replaced the long shipping-route dropdown with:
   - Origin Region: Australia, US, Mozambique, Russia, Indonesia
   - East Coast Discharge Port: Paradip, Visakhapatnam, Gangavaram, Gopalpur, Dhamra, Sagar-Sandheads, Haldia
4. Added 35 origin-to-East-Coast synthetic trade lanes (5 origins × 7 destinations).
5. Added deterministic five-year synthetic historical freight data and feature files for all 35 lanes.
6. Added automatic vessel optimization across Handysize, Supramax, Panamax and Capesize.
7. Vessel selection checks cargo parcel size plus origin/destination:
   - draft
   - LOA
   - beam
   - cargo-handling capability
8. Added multiple-voyage planning when the requested parcel is too large for one feasible vessel.
9. Freight forecasting now uses the selected PS-26006 trade lane's fixed synthetic historical series.
10. Added market-entry timing signals and low-demand/idle-management guidance to the charter decision panel.
11. Kept lightering, cost analysis, Monte Carlo charter-vs-spot analysis and risk indicators connected to the automatically selected vessel.
12. Added an API endpoint: `POST /api/recommend-vessel`.

## Important prototype note

The historical freight series and port constraint figures included in this repository are synthetic/demo inputs for SIH prototyping. They should be replaced with SAIL-approved/live operational data before production use.

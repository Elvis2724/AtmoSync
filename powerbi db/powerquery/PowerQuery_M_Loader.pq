// ============================================================================
// AtmoSync: Power Query (M) Script for Power BI Desktop
// Instructions:
//   1. Open Power BI Desktop -> Get Data -> Blank Query -> Advanced Editor
//   2. Paste the block for `Fact_Spoilage_Arbitrage` (and repeat for `Fact_IoT_Telemetry`, `Dim_Commodities`, `Dim_Markets`)
// ============================================================================

let
    DatasetFolder = "c:\Users\fthom\Desktop\atmosync777\powerbi db\datasets\",
    Source = Csv.Document(
        File.Contents(DatasetFolder & "Fact_Spoilage_Arbitrage.csv"),
        [Delimiter=",", Columns=38, Encoding=65001, QuoteStyle=QuoteStyle.None]
    ),
    PromotedHeaders = Table.PromoteHeaders(Source, [PromoteAllScalars=true]),
    TypedTable = Table.TransformColumnTypes(
        PromotedHeaders,
        {
            {"container_id", type text},
            {"vessel_or_carrier", type text},
            {"commodity_id", type text},
            {"commodity_name", type text},
            {"category", type text},
            {"origin_name", type text},
            {"current_lat", type number},
            {"current_lon", type number},
            {"speed_kmh", type number},
            {"temp_c", type number},
            {"optimal_temp_c", type number},
            {"max_safe_temp_c", type number},
            {"humidity_pct", type number},
            {"vibration_g", type number},
            {"co2_ppm", type number},
            {"ethylene_ppm", type number},
            {"compressor_status", type text},
            {"quality_remaining_pct", type number},
            {"degradation_multiplier", type number},
            {"burn_rate_pct_per_hr", type number},
            {"time_to_spoilage_hrs", type number},
            {"base_cargo_value_usd", Currency.Type},
            {"primary_market_id", type text},
            {"primary_market_name", type text},
            {"primary_distance_km", type number},
            {"primary_eta_hrs", type number},
            {"primary_arrival_quality_pct", type number},
            {"primary_expected_value_usd", Currency.Type},
            {"recommended_secondary_id", type text},
            {"recommended_secondary_market", type text},
            {"secondary_distance_km", type number},
            {"secondary_eta_hrs", type number},
            {"secondary_arrival_quality_pct", type number},
            {"secondary_net_value_usd", Currency.Type},
            {"spoilage_arbitrage_usd", Currency.Type},
            {"risk_status", type text},
            {"recommended_action", type text},
            {"last_updated", type datetimezone}
        }
    )
in
    TypedTable

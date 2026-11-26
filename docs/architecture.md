# AtmoSync System Architecture

## 1. Data Ingestion & Simulation Layer (`data/` & `backend/atmosync_engine.py`)
- Loads reference commodity profiles (`data/commodities.json`), global market ports (`data/markets.json`), and active reefer container fleet telemetry (`data/fleet_containers.json`).
- Emits synthetic Apache Kafka telemetry events on topic `iot.reefer.telemetry.v1` every 3 seconds with internal temperature (°C), relative humidity (%), vibration shock (G), $\text{CO}_2$ (ppm), ethylene ($\text{C}_2\text{H}_4$ ppm), and vessel GPS coordinates.

## 2. ELT Warehouse & dbt Transformation Layer (`powerbi db/database/` & `dbt/`)
- **Raw Landing (`raw_iot_stream`)**: Stores incoming Kafka JSON events with partition and offset metadata.
- **Staging (`stg_telemetry` / `dbt/models/stg_iot_telemetry.sql`)**: Parses JSON sensor attributes, casts types, and filters out corrupted sensor spikes.
- **Analytical Mart (`mart_spoilage_arbitrage` / `dbt/models/mart_spoilage_arbitrage.sql`)**: Joins live telemetry with commodity $Q_{10}$ kinetic parameters and port distances to compute real-time spoilage arbitrage margins.

## 3. Quantitative Arbitrage Calculator (`backend/arbitrage_calculator.py`)
- Computes thermal, humidity, and vibration degradation multipliers.
- Evaluates arrival cargo quality at the **Primary Destination Port** vs. **Candidate Secondary Ports** (accounting for spot price multipliers and port diversion fees).
- Triggers automated alerts to `#trading-arbitrage-alerts` when net reroute alpha exceeds \$20,000.

## 4. Presentation & BI Layer (`frontend/` & `powerbi db/`)
- **Web Trading Terminal (`frontend/`)**: Interactive SVG global route map, HTML5 Canvas degradation curves, and one-click reroute execution matrix.
- **Power BI Star-Schema (`powerbi db/`)**: Auto-updated CSV fact/dimension tables, DAX measures library, Power Query M loader, and custom dark theme.



- Diabetes Progression Prediction: Leveraging Machine Learning for Proactive HealthcareChronic diseases such as diabetes pose a growing global health challenge, affecting millions of individuals and placing sustained pressure on healthc
- are systems. While traditional clinical practice often relies on threshold-based diagnostic markers to identify whether a patient has diabetes, managing the condition eff
- e
- c
- tively requires understanding how rapidly it is likely to advance. The Diabetes Progr
- e
- ssion Prediction project addresses this gap by applying supervised machine learning techniques to estimate a patient's quantitative disease progression over a one-year horizon using baseline clinical, demographic, and metabolic indicators.At the core of the project is a shift from reactive diagnosis to proactive ris
-


-
-
-  k
-   stratification. Two pati
- ent
- s with comparable baseline blood glucose levels may experience vastly different clinical trajectories due to underlying variations in body mass index (BMI), blood pressure, lipid profiles, and serum biomarkers. By modeling disease progression as a continuous regression problem rather than a binary classification task, the system provides a granular risk score. Such qua
- n
- 
- t

-
-  i
- t
- ative insights allow clinicians and care teams to identify high-risk individuals early and prioritize targeted lifestyle modifications, closer monitoring, or timely therapeutic adjustments before severe complications develop.To build a reliable predictive framework, the project follows a disciplined data science workflow grounded in statistical rigor and reproducibility. Using Python and core anal
- y
- 
- 

- t
-
-  ical libraries such as Pandas, NumPy, and Scikit-learn, the workflow begins with exploratory data analysis to examine feature distributions, detect outliers, and evaluate multicollinearity among correlated metabolic variables. Because clinical datasets are sensitive to data leakage, all preprocessing steps—including missing-value imputation and feature scaling via StandardScaler—are encapsulated wit
-  
-
-
- hin cross-validation folds. Multiple regression architectures are then benchmarked systematically, comparing regularized linear models like Ridge and Lasso against non-linear ensemble methods such as XGBoost and LightGBM. Model performance is evaluated across k-fold cross-validation using Root Mean Squared Error (RMSE), Mean Absolute Error (MAE), and the coefficient of determination ($R^2$).Equally cri
- t
- i
- c
- al in healthcare analytics is model transparency. High predictive accuracy alone is insufficient if clinicians cannot understand why a model assigns a particular risk score. To bridge this gap, the project incorporates SHAP (SHapley Additive exPlanations) to decompose individual predictions into feature-level contributions, confirming that key drivers such as BMI and specific serum markers align wit
-
- h
-
-  established
- m

- edical knowledge. Furthermore, wrapping the trained pipeline into an interactive Streamlit or FastAPI application demonstrates how analytical models can transition from static notebooks into accessible decision-support prototypes.Ultimately, the Diabetes Progression Prediction project illustrates how structured machine learning engineering can transform routine clinical measurements int

- o

-  actionable foresight. While predictive models built on observational data cannot replace clinical judgment or establish causal mechanisms, they serve as valuable analytical aids—helping healthcare providers move closer to personalized, preventive care.


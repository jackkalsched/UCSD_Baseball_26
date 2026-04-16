# Experimental Models & Sandbox Environment
This directory is designed exclusively for prototyping, evaluating, and testing custom analytics logic and unverified binary models (`.pkl`) independently before merging them into the fully integrated `/analytics_suite`. 

### Best Practices for Testing Models:
1. **Isolated State:** Perform experimental dataframe manipulations here to prevent mistakenly overwriting your functional BigQuery pulls or `static/data` artifacts that interface the web application. 
2. **Accessing Core Functions:** You can safely import functional tools from the broader application (like `run_expectancy`) using the dynamically injected system path templates found in the `scratchpads/` examples.
3. **Transition to Suite:** Once an experiment is optimized and functionally correct, migrate the models to their dedicated category like `analytics_suite/pitching/models/` and package your functions inside `analytics_suite/pitching/*.py`!

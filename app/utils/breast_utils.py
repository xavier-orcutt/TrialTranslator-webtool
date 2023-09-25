import csv
import numpy as np
import math
import pandas as pd

# Get list of variables for lung model
with open('data/breast_columns.csv', 'r') as csv_file:
    csv_reader = csv.reader(csv_file)
    for row in csv_reader:
        breast_columns = [str(item) for item in row]

# Function to extract form data and store it in a list
def extract_breast_data(form):
    
    # Create empty list where processed data will be placed into 
    form_data = []

    # Collect from data from PracticeType up to pdl1_n
    for var in breast_columns[0:28]:
        var_value = form.get(var)
        form_data.append(var_value)

    # Convert met_year from string to int and reinsert into list 
    met_year_int = int(form_data[7])
    form_data[7] = met_year_int

    # Process insurance data 
    insurance = form.getlist('insurance')
    processed_insurance = process_insurance(insurance_data = insurance)
    form_data.extend(processed_insurance)

    # Collect from data from ecog_diagnosis up to bmi_diag
    for var in breast_columns[36:39]:
        var_value = form.get(var)
        form_data.append(var_value)

    form_data.append("0") #bmi_diag_na will never be missing 
    
    weight_pct_change_value = form.get('weight_pct_change')
    form_data.extend([weight_pct_change_value, "0", weight_pct_change_value]) #weight_pct_change_na will never be missing and impute weight_pct_change for weight_slope  

    lab_diag = []
    # Collect albumin_diag to wbc_diag
    for var in breast_columns[43:59]:
        var_value = form.get(var)
        lab_diag.append(var_value)

    # Replace '' with np.nan
    lab_diag_processed = [np.nan if item == "" else item for item in lab_diag]

    # Convert str to float; leave np.nan alone. 
    lab_diag_int = [float(x) if isinstance(x, str) else x for x in lab_diag_processed]

    # Multiply albumin by 10 due to unit conversion 
    lab_diag_int[0] *= 10

    na_labs = []
    for x in lab_diag_int:
        if math.isnan(x):
            na_labs.append('1')
        else:
            na_labs.append('0')

    form_data.extend(lab_diag_int)
    form_data.extend(na_labs)

    lab_sum = []
    # Collect alp_max to wbc_min
    for var in breast_columns[75:88]:
        var_value = form.get(var)
        lab_sum.append(var_value)

    # Replace '' with np.nan
    lab_sum_processed = [np.nan if item == "" else item for item in lab_sum]

    # Convert str to float; leave np.nan alone. 
    lab_sum_int = [float(x) if isinstance(x, str) else x for x in lab_sum_processed]

    # Multiply albumin by 10 due to unit conversion 
    lab_sum_int[7] *= 10

    na_labs_sum = []
    for x in lab_sum_int:
        if math.isnan(x):
            na_labs_sum.append('1')
        else:
            na_labs_sum.append('0')

    form_data.extend(lab_sum_int) # extend na_labs_sum at the very end

    pmh = []
    # Collect from chf up to other cancer
    for var in breast_columns[88:122]:
        var_value = form.get(var)
        pmh.append(var_value)

    # Replace None for metastatic_cancer with 1
    pmh[18] = 1  

     # solid_tumor_wihtout_mets = 0 if stage at first diagnosis is IV
    if form_data[6] == "IV":
        pmh[19] = 0
    else: 
        pmh[19] = 1

    form_data.extend(pmh)

    # Process site of metastasis 
    met_site = form.getlist('met_site')
    processed_met_site = process_met_site(met_site)
    form_data.extend(processed_met_site)

    # Process ses and convert to float
    ses = form.get('ses')
    ses_int = float(ses)

    form_data.append(ses_int)

    # _na column for summary labs added to the end
    form_data.extend(na_labs_sum)

    return form_data

def process_insurance(insurance_data):
    # Define the list of possible insurance options
    insurance_options = ['medicare',
                         'medicaid',
                         'medicare_medicaid',
                         'commercial',
                         'patient_assistance',
                         'other_govt',
                         'self_pay',
                         'other']

    # Initialize the result list with zeros
    result = [0] * len(insurance_options)

    # Iterate through the options and check if they are selected in form_data
    for i, option in enumerate(insurance_options):
        if option in insurance_data:
            result[i] = 1

    return result

def process_met_site(met_site_data):
    # Define the list of possible insurance options
    met_site_options = ['bone_met',
                        'thorax_met',
                        'lymph_met',
                        'liver_met',
                        'cns_met',
                        'skin_met', 
                        'peritoneum_met',
                        'other_met']

    # Initialize the result list with zeros
    result = [0] * len(met_site_options)

    # Iterate through the options and check if they are selected in form_data
    for i, option in enumerate(met_site_options):
        if option in met_site_data:
            result[i] = 1

    return result

risk_cutoff_breast = pd.read_csv('data/risk_cutoff_breast.csv', index_col = 0)
def categorize_breast_risk(trials, risk_score):
    risk_list = []
    for x in trials: 
        if risk_score >= risk_cutoff_breast.loc[x].high:
            risk_list.append('HIGH')
        elif risk_score <= risk_cutoff_breast.loc[x].low:
            risk_list.append('LOW')
        else:
            risk_list.append('MEDIUM')

    return risk_list
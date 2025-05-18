#!/usr/bin/env python
# coding: utf-8

# In[1]:


import pandas as pd
import ipywidgets as widgets
from IPython.display import display, clear_output, HTML
import plotly.express as px
import numpy as np
import os
from datetime import datetime

# --- Backend Save Directory ---
SAVE_DIR = "submissions"
os.makedirs(SAVE_DIR, exist_ok=True)

# --- Helper Functions ---

def parse_file(file_path_or_buffer):
    try:
        df = pd.read_excel(file_path_or_buffer)
        if df.shape[1] == 1:
            file_path_or_buffer.seek(0)
            df = pd.read_csv(file_path_or_buffer)
    except Exception:
        file_path_or_buffer.seek(0)
        df = pd.read_csv(file_path_or_buffer)
    return df

def save_submission(form_data, file_bytes, filename):
    # Save form data
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    userfile = os.path.join(SAVE_DIR, f"{form_data['Name']}_{timestamp}.txt")
    with open(userfile, "w") as f:
        for k, v in form_data.items():
            f.write(f"{k}: {v}\n")
    # Save uploaded file
    file_path = os.path.join(SAVE_DIR, f"{form_data['Name']}_{timestamp}_{filename}")
    with open(file_path, "wb") as f:
        f.write(file_bytes)
    return userfile, file_path

# --- User Form Widgets ---

name = widgets.Text(description="Name:", style={'description_width': 'initial'}, layout=widgets.Layout(width="50%"))
email = widgets.Text(description="Email:", style={'description_width': 'initial'}, layout=widgets.Layout(width="50%"))
phone = widgets.Text(description="Phone:", style={'description_width': 'initial'}, layout=widgets.Layout(width="50%"))
company = widgets.Text(description="Company:", style={'description_width': 'initial'}, layout=widgets.Layout(width="50%"))
upload = widgets.FileUpload(accept='.xlsx,.xls,.csv', multiple=False, description="Upload Excel/CSV")

form_items = widgets.VBox([
    widgets.HTML("<h3>HR Attrition Dashboard Submission Form</h3>"),
    name, email, phone, company, upload
])

submit_btn = widgets.Button(description="Submit & Analyze", button_style='success')
form_out = widgets.Output()
dashboard_out = widgets.Output()

display(form_items, submit_btn, form_out, dashboard_out)

# --- Main Submission Handler ---

def on_submit_clicked(b):
    with form_out:
        clear_output()
        # Validate
        if not name.value or not email.value or not phone.value or len(upload.value) == 0:
            print("Please fill all fields and upload a file.")
            return
        # Parse file
        file_info = next(iter(upload.value.values()))
        file_bytes = file_info['content']
        filename = file_info['metadata']['name']
        from io import BytesIO
        file_like = BytesIO(file_bytes)
        file_like.name = filename
        try:
            df = parse_file(file_like)
        except Exception as e:
            print("Could not read file:", e)
            return
        if df is None or df.empty:
            print("Uploaded file is empty or invalid.")
            return
        # Save submission
        form_data = {
            "Name": name.value,
            "Email": email.value,
            "Phone": phone.value,
            "Company": company.value,
            "Filename": filename
        }
        save_submission(form_data, file_bytes, filename)
        print("Submission saved. Generating dashboard...")
        # Show dashboard
        with dashboard_out:
            clear_output()
            show_dashboard(df)

submit_btn.on_click(on_submit_clicked)

# --- Dashboard Display ---

def show_dashboard(df):
    # Only show filters and charts for available columns
    filters = []
    filter_widgets = {}
    # Department
    if 'Department' in df.columns and df['Department'].notna().any():
        depts = df['Department'].dropna().unique()
        dept_filter = widgets.SelectMultiple(options=depts, value=tuple(depts), description='Department')
        filters.append(dept_filter)
        filter_widgets['Department'] = dept_filter
    # JobRole
    if 'JobRole' in df.columns and df['JobRole'].notna().any():
        roles = df['JobRole'].dropna().unique()
        role_filter = widgets.SelectMultiple(options=roles, value=tuple(roles), description='JobRole')
        filters.append(role_filter)
        filter_widgets['JobRole'] = role_filter
    # Age
    if 'Age' in df.columns and df['Age'].notna().any():
        min_age = int(df['Age'].min())
        max_age = int(df['Age'].max())
        age_slider = widgets.IntRangeSlider(value=[min_age, max_age], min=min_age, max=max_age, step=1, description='Age')
        filters.append(age_slider)
        filter_widgets['Age'] = age_slider
    # Gender
    if 'Gender' in df.columns and df['Gender'].notna().any():
        genders = df['Gender'].dropna().unique()
        gender_filter = widgets.SelectMultiple(options=genders, value=tuple(genders), description='Gender')
        filters.append(gender_filter)
        filter_widgets['Gender'] = gender_filter

    apply_btn = widgets.Button(description="Apply Filters", button_style='primary')
    filters_box = widgets.HBox(filters + [apply_btn])
    dashboard_out2 = widgets.Output()
    display(filters_box, dashboard_out2)
    
    def apply_filters(b):
        with dashboard_out2:
            clear_output()
            dff = df.copy()
            # Apply each filter
            if 'Department' in filter_widgets:
                dff = dff[dff['Department'].isin(filter_widgets['Department'].value)]
            if 'JobRole' in filter_widgets:
                dff = dff[dff['JobRole'].isin(filter_widgets['JobRole'].value)]
            if 'Age' in filter_widgets:
                start, end = filter_widgets['Age'].value
                dff = dff[(dff['Age'] >= start) & (dff['Age'] <= end)]
            if 'Gender' in filter_widgets:
                dff = dff[dff['Gender'].isin(filter_widgets['Gender'].value)]
            show_kpis_and_charts(dff)
    apply_btn.on_click(apply_filters)
    # Show initial
    show_kpis_and_charts(df)

def show_kpis_and_charts(df):
    # KPIs
    kpi_html = "<h4>Key Metrics</h4><table style='width:60%;font-size:1.2em;'>"
    if 'EmployeeNumber' in df.columns:
        kpi_html += f"<tr><td><b>Total Employees</b></td><td>{df['EmployeeNumber'].nunique()}</td></tr>"
    if 'Attrition' in df.columns:
        kpi_html += f"<tr><td><b>Attrition Count</b></td><td>{(df['Attrition']=='Yes').sum()}</td></tr>"
        kpi_html += f"<tr><td><b>Attrition Rate</b></td><td>{100*(df['Attrition']=='Yes').mean():.1f}%</td></tr>"
    if 'JobSatisfaction' in df.columns:
        kpi_html += f"<tr><td><b>Avg. Job Satisfaction</b></td><td>{df['JobSatisfaction'].mean():.2f}</td></tr>"
    if 'PerformanceRating' in df.columns:
        kpi_html += f"<tr><td><b>Avg. Performance Rating</b></td><td>{df['PerformanceRating'].mean():.2f}</td></tr>"
    kpi_html += "</table>"
    display(HTML(kpi_html))

    # Tableau-like charts
    # 1. Attrition Rate by Department
    if 'Department' in df.columns and 'Attrition' in df.columns:
        chart_df = df.groupby('Department')['Attrition'].apply(lambda x: (x=='Yes').mean()).reset_index()
        chart_df.columns = ['Department', 'Attrition Rate']
        fig = px.bar(chart_df, x='Department', y='Attrition Rate', title="Attrition Rate by Department", text='Attrition Rate')
        fig.update_layout(yaxis_tickformat='.0%', height=400)
        fig.show()
    # 2. Job Satisfaction by JobRole
    if 'JobRole' in df.columns and 'JobSatisfaction' in df.columns:
        chart_df = df.groupby('JobRole')['JobSatisfaction'].mean().reset_index()
        fig = px.bar(chart_df, x='JobRole', y='JobSatisfaction', title="Avg. Job Satisfaction by Job Role", text='JobSatisfaction')
        fig.update_layout(height=400)
        fig.show()
    # 3. Age Distribution
    if 'Age' in df.columns:
        fig = px.histogram(df, x='Age', nbins=20, title="Age Distribution")
        fig.update_layout(height=400)
        fig.show()
    # 4. Performance vs Satisfaction
    if set(['PerformanceRating','JobSatisfaction','Department']).issubset(df.columns):
        fig = px.scatter(df, x='PerformanceRating', y='JobSatisfaction', color='Department',
                         hover_data=['EmployeeNumber','JobRole'] if 'JobRole' in df.columns else None,
                         title="Performance vs Job Satisfaction")
        fig.update_layout(height=400)
        fig.show()
    # 5. Employee Table
    cols = [c for c in ['EmployeeNumber','Department','JobRole','PerformanceRating','JobSatisfaction','Attrition'] if c in df.columns]
    if cols:
        display(HTML("<h4>Top Employees (Sample)</h4>"))
        display(df[cols].head(20).style.set_table_attributes('style="width:60%;font-size:1.1em;"'))


# In[ ]:





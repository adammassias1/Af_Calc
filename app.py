import time  # to simulate a real time data, time loop
import numpy as np
import pandas as pd  # read csv, df manipulation
import plotly.express as px  # interactive charts
import streamlit as st  # 🎈 data web app development
import datetime
from datetime import timedelta
from dateutil.relativedelta import relativedelta
from operator import itemgetter
from pandas.tseries.offsets import *


def config_page():
    st.set_page_config(
        page_title="Asset Finance Calc",
        page_icon='RecogniseIcon.png',
        layout="wide",
    )

    st.image('RecogniseBankLogo-removebg-preview.png', width=200)

    # dashboard title
    st.title("Asset Finance Calculator (Under Development)")

def set_params():
    
    global loan_amount, loan_period, balloon_payment, vat_deposit, deposit, doc_fee, option_to_purchase, rent_profile, cof, margin, irr, broker_fee, settlement, vat_deferal_period, day_count_basis, holiday_calendar, start_date, month_end
    #Product = st.selectbox('Product Type', ('Full Amortisation', 'Balloon Payment', 'Full Amortisation with Deposit'))
    st.markdown("**Rental & Repayment Plan**")
    col1, col2, col3 = st.columns([1, 1, 1])
    loan_amount = col1.number_input('Loan Amount',0)
    loan_period = col2.number_input('Loan Period (months)',0)
    deposit = col3.number_input('Deposit (%)',step=1.,format="%.2f")
    col1, col2, col3 = st.columns([1, 1, 1])
    vat_deposit = col1.number_input('Vat Deposit (%)',step=1.,format="%.2f")
    vat_deferal_period = col2.number_input('Vat Deferal Period (months)',0)
    balloon_payment = col3.number_input('Baloon Payment (%)',step=1.,format="%.2f")
    col1, col2, col3 = st.columns([1, 1, 1])
    rent_profile = col1.selectbox('Rent Profile', ('Monthly', 'Quarterly'))
    day_count_basis = col2.selectbox('Day Count Basis', ('ACT/365', '30/365'))
    holiday_calendar = col3.selectbox('Holiday Calendar (under development)', ('LDN', 'Tar'))
    col1, col2, col3 = st.columns([1, 1, 1])
    start_date = col1.date_input('Start Date', datetime.date(2022,8,1))
    month_end = col2.checkbox('month-end calculation')
    st.markdown("**Interest Rate**")
    col1, col2, col3 = st.columns([1, 1, 1])
    cof = col1.number_input('COF (%)',step=1.,format="%.5f")
    margin = col2.number_input('Margin (%)',step=1.,format="%.5f")
    settlement = col3.number_input('Settlement Rate (%)',step=1.,format="%.2f")
    col1, col2, col3 = st.columns([1, 1, 1])
    irr = cof + margin
    col1.write(f"The IRR is {round(irr, 5) * 100}%")
    #irr = col1.number_input('IRR',step=1.,format="%.5f")
    st.markdown("**Fees**")
    col1, col2, col3 = st.columns([1, 1, 1])
    option_to_purchase = col1.number_input('Option To Purchase Fee',0)
    broker_fee = col2.number_input('Broker Fee',0)
    doc_fee = col3.number_input('Doc Fee',0)

def create_payment_schedule_df():

    df = pd.DataFrame(columns = ['Date', 'B/F', 'VAT', 'VAT Deposit', 'Baloon Payment', 'Deposit', 'Broker Fee', 'Doc Fee', 'Rents', 'COF', 'Margin', 'C/F', 'Settlement'])
    
    end = start_date + relativedelta(months=loan_period + 1)
    if month_end:
        df['Date'] = pd.date_range(start_date, end, freq='BM')
    elif start_date.day == 31:
        df['Date'] = pd.date_range(start_date, end, freq='BM')
    elif start_date.day == 30 or start_date.day == 29:
        df['Date'] = pd.date_range(start_date - relativedelta(months = 1), end - relativedelta(months = 1), freq='MS').shift(int(start_date.strftime("%d")) - 1, freq = 'd')
        for i in range(1, len(df['Date'])-1):
            if df.loc[i,'Date'].day < 4:
                df.loc[i,'Date'] = df.loc[i,'Date'] - timedelta(days = df.loc[i,'Date'].day)
            else: 
                pass

        df['Date'] = df['Date'].apply(lambda x: x - timedelta(days = 1) if x.weekday() == 5 else x - timedelta(days = 2) if x.weekday() == 6 else x)
    else:
        df['Date'] = pd.date_range(start_date - relativedelta(months = 1), end- relativedelta(months = 1), freq='MS').shift(int(start_date.strftime("%d")) - 1, freq = 'd')
        df['Date'] =  df['Date'].apply(lambda x: x - timedelta(days = 1) if x.weekday() == 5 else x - timedelta(days = 2) if x.weekday() == 6 else x)

    return {'df' : df}


def alpha_gen():
    
    df = itemgetter('df')(create_payment_schedule_df())

    alpha = [None] * len(df['Date'])
    for i in range(1, len(df['Date'])):
        if day_count_basis == 'ACT/365':
            alpha[i] = irr * ((df.loc[i,'Date'] - df.loc[i - 1,'Date']).days) / 365
        else:
            alpha[i] = irr * (30) / 365
    
    return {'alpha' : alpha}

#Rents on loan amount
def rents_calc():
    alpha = itemgetter('alpha')(alpha_gen())
    
    rents = (1/(1+alpha[len(alpha) - 1]))
    for n in reversed(range(1, len(alpha) - 1)):
        rents += 1
        rents *= 1/(1+alpha[n])
    
    return {'rents' : rents}


#----------------------------------------------------------------------------------------------
def create_payment_schedule_input():
    
    df = itemgetter('df')(create_payment_schedule_df())
    rents = itemgetter('rents')(rents_calc())
    alpha = itemgetter('alpha')(alpha_gen())

    reduction_vat = 1
    reduction_baloon = 1
    if st.button('Calculate Payment Schedule'):
        for i in range(1, vat_deferal_period + 1):
            reduction_vat *= (1 + alpha[i])
        for i in range(1, loan_period + 1):
            reduction_baloon *= (1 + alpha[i])
        df['Rents'] = (((loan_amount)*(1 + vat_deposit) + broker_fee - (deposit*loan_amount) + doc_fee) - ((loan_amount*vat_deposit)/reduction_vat) - ((loan_amount*balloon_payment)/reduction_baloon)) * (1 / rents)
        

        df.loc[0,'Rents'] = 0
        df.loc[loan_period, 'Baloon Payment'] = balloon_payment * loan_amount
        df.loc[0,'VAT'] = - vat_deposit * loan_amount
        df.loc[0,'Deposit'] = deposit*loan_amount
        df.loc[vat_deferal_period, 'VAT Deposit'] = vat_deposit * loan_amount
        #df.loc[0,'B/F'] = - loan_amount
        df.loc[0,'Broker Fee'] = - broker_fee
        df.loc[0,'Doc Fee'] = - doc_fee
        df.loc[0,'B/F'] = - loan_amount
        df.loc[0,'COF'] = 0
        df.loc[0,'Margin'] = 0
        df = df.fillna(0)
        df.loc[0,'C/F'] = df.loc[0,'B/F'] + df.loc[0,'VAT'] + df.loc[0,'VAT Deposit'] + df.loc[0,'Deposit'] + df.loc[0,'Rents'] + df.loc[0,'COF'] + df.loc[0,'Margin'] + df.loc[0, 'Broker Fee'] + df.loc[0, 'Doc Fee']

        for i in range(1,len(df['Date'])):
            df.loc[i,'B/F'] = df.loc[i - 1,'C/F']
            if day_count_basis == 'ACT/365':
                df.loc[i,'COF'] = df.loc[i - 1,'C/F']*((df.loc[i,'Date'] - df.loc[i - 1,'Date']).days)/365 * cof
                df.loc[i,'Margin'] = df.loc[i - 1,'C/F']*((df.loc[i,'Date'] - df.loc[i - 1,'Date']).days)/365 * margin
            else:
                df.loc[i,'COF'] = df.loc[i - 1,'C/F']*(30)/365 * cof
                df.loc[i,'Margin'] = df.loc[i - 1,'C/F']*(30)/365 * margin
            df.loc[i,'C/F'] = df.loc[i,'B/F'] + df.loc[i,'VAT'] + df.loc[i,'VAT Deposit'] + df.loc[i,'Deposit'] + df.loc[i,'Rents'] + df.loc[i,'COF'] + df.loc[i,'Margin'] + df.loc[i, 'Baloon Payment']
            
        for j in range(1, len(df['Date'])):
            for i in range(j, len(df['Date'])):
                df.loc[j, 'Settlement'] += df.loc[i, 'Rents'] / ((1.0 + settlement)**((df.loc[i, 'Date'] - df.loc[j, 'Date']).days / 365.0)) + df.loc[i, 'Baloon Payment'] / ((1.0 + settlement)**((df.loc[i, 'Date'] - df.loc[j, 'Date']).days / 365.0)) + df.loc[i, 'VAT Deposit'] / ((1.0 + settlement)**((df.loc[i, 'Date'] - df.loc[1, 'Date']).days / 365.0))

        st.markdown(f"**Fully amortised loan over {loan_period} months, an amount of £{loan_amount}, a {deposit*100}% deposit, a {balloon_payment*100}% baloon payment and a {vat_deferal_period} months VAT deferal period**")

        st.table(df.style.set_precision(1))

def main():
    config_page()
    set_params()
    try:
        create_payment_schedule_input()
    except:
        st.markdown('**Please fill in all required parameters**')

if __name__ == "__main__":
    main()
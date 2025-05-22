import streamlit as st
import pandas as pd
import re
import time
import random
import os
import requests
from apify_client import ApifyClient
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium_stealth import stealth

# --- API KEYS ---
API_TOKEN = os.getenv("apify_api")
ACTOR_ID = os.getenv("actor_id")
WHATCMS_API = os.getenv("whatcms_api")

# Create Selenium Driver
def create_driver():
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64)")
    driver = webdriver.Chrome(options=options)
    stealth(driver,
        languages=["en-US", "en"],
        vendor="Google Inc.",
        platform="Win32",
        webgl_vendor="Intel Inc.",
        renderer="Intel Iris OpenGL Engine",
        fix_hairline=True,
    )
    return driver

# Engagement Rate Function
def get_engagement_rate(username):
    try:
        driver = create_driver()
        driver.get("https://www.clickanalytic.com/free-instagram-engagement-calculator/")
        input_box = WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.ID, "username"))
        )
        input_box.clear()
        input_box.send_keys(username)
        submit_btn = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Check Engagement Rate')]"))
        )
        submit_btn.click()

        result_block = WebDriverWait(driver, 15).until(
            EC.visibility_of_element_located((By.XPATH, "//div[contains(@class,'et_pb_text_inner') and contains(.,'%')]"))
        )

        match = re.search(r"\d+\.?\d*%", result_block.text)
        rate = match.group(0) if match else ""
        driver.quit()
        return rate
    except Exception as e:
        driver.quit()
        return f"Error: {e}"

# Apify Instagram Info Function
def fetch_instagram_info(usernames):
    client = ApifyClient(API_TOKEN)
    run = client.actor(ACTOR_ID).call(run_input={"usernames": usernames})
    info = {}
    for item in client.dataset(run["defaultDatasetId"]).iterate_items():
        u = item.get("username")
        if u:
            info[u] = item
    return info

# DuckDuckGo Top 3 Links
def fetch_top_links(query):
    try:
        driver = create_driver()
        driver.get("https://html.duckduckgo.com/html/")

        search_bar = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "search_form_input_homepage"))
        )
        search_bar.clear()
        search_bar.send_keys(query)
        driver.find_element(By.ID, "search_button_homepage").click()

        results = WebDriverWait(driver, 10).until(
            EC.presence_of_all_elements_located((By.CSS_SELECTOR, "a.result__url"))
        )

        top_links = []
        for result in results:
            href = result.get_attribute("href")
            if href and not any(domain in href for domain in ["instagram.com", "twitter.com", "x.com", "youtube.com", "youtu.be"]):
                top_links.append(href)
            if len(top_links) == 3:
                break

        driver.quit()
        return top_links
    except Exception as e:
        driver.quit()
        return [f"Error: {e}"]

# WhatCMS Detection
def detect_cms(url):
    try:
        response = requests.get(
            "https://whatcms.org/APIEndpoint/Detect",
            params={
                "key": WHATCMS_API,
                "url": url
            },
            timeout=10
        )
        data = response.json()
        if data.get("result", {}).get("code") == 200:
            cms = data["result"].get("name", "Unknown")
            confidence = data["result"].get("confidence", "N/A")
            return cms, confidence
        else:
            return "Unknown", "N/A"
    except Exception as e:
        return f"Error: {e}", "N/A"

# -------------------- Streamlit UI --------------------

st.set_page_config(page_title="Instagram & Designer Info", layout="centered")
st.title("🎯 Instagram & Designer Intelligence Tool")

# Instagram Info
st.header("📸 Instagram Handle Lookup")
insta_usernames = st.text_area("Enter Instagram Handles (comma separated)", "").strip()

if st.button("Fetch Instagram Info"):
    usernames = [u.strip().lstrip('@') for u in insta_usernames.split(",") if u.strip()]
    if usernames:
        info = fetch_instagram_info(usernames)
        df = pd.DataFrame([
            {
                "Username": u,
                "Full Name": info[u].get("fullName"),
                "Followers": info[u].get("followersCount"),
                "Following": info[u].get("followsCount"),
                "Verified": info[u].get("verified"),
                "Business": info[u].get("isBusinessAccount"),
                "Joined Recently": info[u].get("joinedRecently"),
                "URL": info[u].get("url"),
                "Bio": info[u].get("biography")
            } for u in usernames if u in info
        ])
        st.dataframe(df)

# Engagement Rate
st.header("📊 Engagement Rate Calculator")
username = st.text_input("Enter Instagram Handle (single)")
if st.button("Calculate Engagement Rate"):
    clean_user = username.strip().lstrip("@")
    if clean_user:
        rate = get_engagement_rate(clean_user)
        st.success(f"Engagement Rate: {rate}")

# Designer Search and CMS Check
# Designer Search and CMS Check
st.header("🎨 Designer Search Links + CMS Detection")
designer_names = st.text_area("Enter Designer Names (one per line)", "")

if "cms_results" not in st.session_state:
    st.session_state.cms_results = {}

if "selected_links" not in st.session_state:
    st.session_state.selected_links = {}

if st.button("Search Designers"):
    names = [n.strip() for n in designer_names.strip().split("\n") if n.strip()]
    st.session_state.search_results = {}

    for name in names:
        links = fetch_top_links(f"{name} designer official website")
        st.session_state.search_results[name] = links

# Show search results and CMS detection
if "search_results" in st.session_state:
    for name, links in st.session_state.search_results.items():
        if links:
            st.subheader(f"{name}")
            selected_link = st.radio(f"Top links for {name}", links, key=f"radio_{name}")
            st.session_state.selected_links[name] = selected_link

            if (name, selected_link) not in st.session_state.cms_results:
                cms, confidence = detect_cms(selected_link)
                st.session_state.cms_results[(name, selected_link)] = (cms, confidence)

            cms, confidence = st.session_state.cms_results.get((name, selected_link), ("Unknown", "N/A"))
            st.write(f"**Selected Link:** [{selected_link}]({selected_link})")
            st.write(f"**CMS:** {cms} | **Confidence:** {confidence}")
        else:
            st.warning(f"No valid links found for {name}.")
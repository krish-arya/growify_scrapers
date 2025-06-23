# 🎯 Instagram & Designer Intelligence Tool

This is a **Streamlit-based web app** designed to help users gather detailed insights on Instagram handles and fashion designers. It automates data collection using web scraping, public APIs, and intelligent searches to assist in influencer research, marketing analysis, and brand discovery.

---

## 🚀 Features

- 📸 **Instagram Handle Lookup**: Fetch profile data such as follower count, bio, verification status, business account status, and more using Apify.
- 📊 **Engagement Rate Calculator**: Calculate Instagram engagement rates using a headless Selenium automation of ClickAnalytic.
- 🔍 **Designer Website Search**: Search for designer websites using DuckDuckGo and retrieve the top 3 relevant links.
- 🧠 **CMS Detection**: Identify the Content Management System (CMS) used by designer websites via WhatCMS API.

---

## 🛠️ Tech Stack

- **Frontend/UI**: Streamlit
- **Automation & Scraping**: Selenium + selenium-stealth
- **External APIs**: Apify, ClickAnalytic (via Selenium), WhatCMS
- **Search Engine**: DuckDuckGo HTML interface
- **Browser Driver**: Headless Chrome

---

## 📦 Installation

1. **Clone the repository**

    ```bash
    git clone https://github.com/yourusername/insta-designer-intelligence.git
    cd insta-designer-intelligence
    ```

2. **Install dependencies**

    ```bash
    pip install -r requirements.txt
    ```

3. **Set environment variables**

    Create a `.env` file in the project root with the following contents:

    ```env
    apify_api=your_apify_api_token
    actor_id=your_apify_actor_id
    whatcms_api=your_whatcms_api_key
    ```

    Or set them in your terminal for a temporary session:

    ```bash
    export apify_api=your_apify_api_token
    export actor_id=your_apify_actor_id
    export whatcms_api=your_whatcms_api_key
    ```

4. **Run the Streamlit app**

    ```bash
    streamlit run app.py
    ```

---

## 🧪 Example Use Cases

- Analyze influencer engagement before marketing outreach.
- Discover and verify designer brand official websites.
- Identify technology stack used by eCommerce brands (e.g., Shopify, WooCommerce).
- Build datasets of verified, high-engagement Instagram handles.

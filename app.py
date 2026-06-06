import streamlit as st
import psycopg2
import pandas as pd
import matplotlib.pyplot as plt

DB_NAME = "sales_hub"
DB_USER = "postgres"
DB_PASSWORD = "admin123"
DB_HOST = "localhost"


def get_connection():
    return psycopg2.connect(
        host=DB_HOST,
        database=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD
    )


st.title("Sales Management System")

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if "role" not in st.session_state:
    st.session_state.role = ""

if "branch_id" not in st.session_state:
    st.session_state.branch_id = None


if not st.session_state.logged_in:

    username = st.text_input("Username", key="username")
    password = st.text_input("Password", type="password", key="password")

    if st.button("Login", key="login_btn"):
        try:
            conn = get_connection()
            cur = conn.cursor()

            cur.execute(
                "SELECT role, branch_id FROM users WHERE username=%s AND password=%s",
                (username, password)
            )

            user = cur.fetchone()

            if user:
                st.session_state.logged_in = True
                st.session_state.role = user[0]
                st.session_state.branch_id = user[1]
                st.rerun()
            else:
                st.error("Invalid Username or Password")

            cur.close()
            conn.close()

        except Exception as e:
            st.error(f"Database Error: {e}")


else:

    st.subheader("Dashboard")
    st.write(f"Welcome {st.session_state.role}")

    if st.session_state.role == "Super Admin":
        st.success("Access: All Branches")
    else:
        st.info("Access: Assigned Branch Only")

    if st.button("Logout", key="logout_btn"):
        st.session_state.logged_in = False
        st.session_state.role = ""
        st.session_state.branch_id = None
        st.rerun()

    # SALES FILTERS
    st.markdown("### Sales Data Filters")

    if st.session_state.role == "Super Admin":
        filter_branch = st.selectbox("Branch", [1, 2], key="filter_branch")
    else:
        filter_branch = st.session_state.branch_id
        st.write(f"Branch ID: {filter_branch}")

    filter_product = st.selectbox(
        "Product Name",
        ["All", "DS", "DA", "BA", "FSD"],
        key="filter_product"
    )

    start_date = st.date_input("Start Date", key="start_date")
    end_date = st.date_input("End Date", key="end_date")

    # VIEW ALL SALES
    if st.button("View All Sales", key="view_all_sales"):

        conn = get_connection()

        if st.session_state.role == "Super Admin":
            query = "SELECT * FROM customer_sales ORDER BY sale_id"
            data = pd.read_sql(query, conn)
        else:
            query = "SELECT * FROM customer_sales WHERE branch_id = %s ORDER BY sale_id"
            data = pd.read_sql(query, conn, params=[st.session_state.branch_id])

        st.dataframe(data)
        conn.close()

    # VIEW FILTERED SALES
    if st.button("View Filtered Sales", key="view_filtered_sales"):

        conn = get_connection()

        if filter_product == "All":
            query = """
            SELECT *
            FROM customer_sales
            WHERE branch_id = %s
            AND sale_date BETWEEN %s AND %s
            ORDER BY sale_id
            """

            data = pd.read_sql(
                query,
                conn,
                params=[filter_branch, start_date, end_date]
            )

        else:
            query = """
            SELECT *
            FROM customer_sales
            WHERE branch_id = %s
            AND product_name = %s
            AND sale_date BETWEEN %s AND %s
            ORDER BY sale_id
            """

            data = pd.read_sql(
                query,
                conn,
                params=[filter_branch, filter_product, start_date, end_date]
            )

        st.dataframe(data)
        conn.close()

    # ADD SALES
    st.markdown("### Add Sales Entry")

    if st.session_state.role == "Super Admin":
        branch_id = st.selectbox("Branch", [1, 2], key="branch_select")
    else:
        branch_id = st.session_state.branch_id
        st.write(f"Branch ID: {branch_id}")

    sale_date = st.date_input("Sale Date", key="sale_date")
    customer_name = st.text_input("Customer Name", key="customer_name")
    mobile_number = st.text_input("Mobile Number", key="mobile_number")

    product_name = st.selectbox(
        "Product",
        ["DS", "DA", "BA", "FSD"],
        key="product_name"
    )

    gross_sales = st.number_input(
        "Gross Sales Amount",
        min_value=0.0,
        key="gross_sales"
    )

    if st.button("Save Sale", key="save_sale"):
        try:
            conn = get_connection()
            cur = conn.cursor()

            cur.execute("""
                INSERT INTO customer_sales
                (branch_id, sale_date, name, mobile_number, product_name, gross_sales)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (
                branch_id,
                sale_date,
                customer_name,
                mobile_number,
                product_name,
                gross_sales
            ))

            conn.commit()
            st.success("Sale Saved Successfully!")

            cur.close()
            conn.close()

        except Exception as e:
            st.error(f"Error: {e}")

    # PAYMENT SPLIT
    st.markdown("### Payment Split")

    sale_id = st.number_input("Sale ID", min_value=1, key="payment_sale_id")
    payment_date = st.date_input("Payment Date", key="payment_date")

    amount_paid = st.number_input(
        "Amount Paid",
        min_value=0.0,
        key="amount_paid"
    )

    payment_method = st.selectbox(
        "Payment Method",
        ["Cash", "UPI", "Card"],
        key="payment_method"
    )

    if st.button("Add Payment", key="add_payment"):
        try:
            conn = get_connection()
            cur = conn.cursor()

            cur.execute("""
                INSERT INTO payment_splits
                (sale_id, payment_date, amount_paid, payment_method)
                VALUES (%s, %s, %s, %s)
            """, (
                sale_id,
                payment_date,
                amount_paid,
                payment_method
            ))

            conn.commit()
            st.success("Payment Added Successfully!")

            cur.close()
            conn.close()

        except Exception as e:
            st.error(f"Error: {e}")

    # PAYMENT REPORT
    st.markdown("### Payment Report")

    if st.button("View Payment Report", key="view_payment_report"):
        conn = get_connection()

        query = """
        SELECT
            sale_id,
            name,
            mobile_number,
            product_name,
            gross_sales,
            received_amount,
            pending_amount,
            status
        FROM customer_sales
        ORDER BY sale_id
        """

        data = pd.read_sql(query, conn)
        st.dataframe(data)
        conn.close()

    # KPI SUMMARY
    st.markdown("### Financial KPI Summary")

    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT
            COALESCE(SUM(gross_sales), 0),
            COALESCE(SUM(received_amount), 0),
            COALESCE(SUM(pending_amount), 0)
        FROM customer_sales
    """)

    result = cur.fetchone()

    col1, col2, col3 = st.columns(3)
    col1.metric("Total Sales", result[0])
    col2.metric("Total Received", result[1])
    col3.metric("Total Pending", result[2])

    cur.close()
    conn.close()

    # BRANCH-WISE TOTAL SALES
    st.markdown("### Branch-wise Total Sales")

    conn = get_connection()

    branch_total_query = """
    SELECT
        b.branch_name,
        SUM(cs.gross_sales) AS total_sales
    FROM customer_sales cs
    JOIN branches b
    ON cs.branch_id = b.branch_id
    GROUP BY b.branch_name
    ORDER BY b.branch_name
    """

    branch_total_data = pd.read_sql(branch_total_query, conn)
    st.dataframe(branch_total_data)

    conn.close()

    # CUSTOMER-WISE TOTAL SALES DETAILS
    st.markdown("### Customer-wise Total Sales Details")

    conn = get_connection()

    customer_total_query = """
    SELECT
        sale_id,
        sale_date,
        name,
        mobile_number,
        product_name,
        gross_sales
    FROM customer_sales
    ORDER BY sale_id
    """

    customer_total_data = pd.read_sql(customer_total_query, conn)
    st.dataframe(customer_total_data)

    conn.close()

    # PAYMENT METHOD SUMMARY
    st.markdown("### Payment Method Summary")

    conn = get_connection()

    payment_query = """
    SELECT
        payment_method,
        SUM(amount_paid) AS total_amount
    FROM payment_splits
    GROUP BY payment_method
    """

    payment_data = pd.read_sql(payment_query, conn)
    st.dataframe(payment_data)
    conn.close()

    if not payment_data.empty:
        st.markdown("### Payment Method Chart")

        fig2, ax2 = plt.subplots()
        ax2.bar(payment_data["payment_method"], payment_data["total_amount"])
        ax2.set_xlabel("Payment Method")
        ax2.set_ylabel("Total Amount")
        ax2.set_title("Payment Method Summary")
        st.pyplot(fig2)

    # BRANCH WISE SALES REPORT
    st.markdown("### Branch-wise Sales Chart Data")

    conn = get_connection()

    branch_query = """
    SELECT
        b.branch_name,
        SUM(cs.gross_sales) AS total_sales
    FROM customer_sales cs
    JOIN branches b ON cs.branch_id = b.branch_id
    GROUP BY b.branch_name
    """

    branch_data = pd.read_sql(branch_query, conn)
    st.dataframe(branch_data)
    conn.close()

    if not branch_data.empty:
        st.markdown("### Branch-wise Sales Chart")

        fig, ax = plt.subplots()
        ax.bar(branch_data["branch_name"], branch_data["total_sales"])
        ax.set_xlabel("Branch")
        ax.set_ylabel("Total Sales")
        ax.set_title("Branch-wise Sales")
        st.pyplot(fig)

    # PENDING PAYMENTS REPORT
    st.markdown("### Pending Payments Report")

    conn = get_connection()

    pending_query = """
    SELECT
        sale_id,
        name,
        mobile_number,
        gross_sales,
        received_amount,
        pending_amount
    FROM customer_sales
    WHERE pending_amount > 0
    """

    pending_data = pd.read_sql(pending_query, conn)
    st.dataframe(pending_data)
    conn.close()

    # SALES STATUS REPORT
    st.markdown("### Sales Status Report")

    conn = get_connection()

    status_query = """
    SELECT
        status,
        COUNT(*) AS total_sales
    FROM customer_sales
    GROUP BY status
    """

    status_data = pd.read_sql(status_query, conn)
    st.dataframe(status_data)
    conn.close()

    if not status_data.empty:
        st.markdown("### Sales Status Pie Chart")

        fig3, ax3 = plt.subplots()
        ax3.pie(
            status_data["total_sales"],
            labels=status_data["status"],
            autopct="%1.1f%%"
        )
        ax3.set_title("Sales Status")
        st.pyplot(fig3)
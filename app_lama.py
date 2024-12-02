from flask import Flask, render_template, request, redirect, url_for, flash
import cx_Oracle

app = Flask(__name__)
app.secret_key = 'saba_1234'

# Konfigurasi koneksi Oracle
dsn = cx_Oracle.makedsn("RTS", 1521, service_name="hclab")
conn = cx_Oracle.connect(user="saba", password="saba", dsn=dsn)

@app.route('/')
def index():
    # Query contoh
    cursor = conn.cursor()
    cursor.execute("SELECT 'Hello, Oracle!' FROM DUAL")
    message = cursor.fetchone()[0]
    cursor.close()

    return render_template('index.html', message=message)


# Route Master Manufacture--------------------------------------------------------------------------------------------------
@app.route('/master_manufacture')
def master_manufacture():
    search_query= request.args.get('search', '')  # Ambil query pencarian dari input
    cursor=conn.cursor()

    if search_query:
        cursor.execute("SELECT manu_id, manu_name, manu_country FROM manufacture WHERE LOWER(manu_name) LIKE :search_query", {
            "search_query": f"%{search_query.lower()}%"
        })
    else:
        cursor.execute("SELECT manu_id, manu_name, manu_country FROM manufacture order by manu_name asc")

    manufactures = [{"manu_id": row[0], "manu_name": row[1], "manu_country": row[2]} for row in cursor.fetchall()]
    cursor.close()

    return render_template('master_manufacture.html', manufactures=manufactures)

    # Route Untuk Tambah Manufacuture
@app.route('/tambah_manufacture', methods=['GET', 'POST'])
def tambah_manufacture():
    if request.method == 'POST':
        # Ambil data dari form
        manu_id = request.form['manu_id']
        manu_name = request.form['manu_name']
        manu_country = request.form['manu_country']

        cursor = conn.cursor()
        # Validasi: Cek apakah manu_id sudah ada
        cursor.execute("SELECT COUNT(*) FROM manufacture WHERE manu_id = :manu_id", {"manu_id": manu_id})
        count = cursor.fetchone()[0]

        if count > 0:
            flash("Manufacture ID sudah ada. Gunakan ID yang lain.", "danger")
            cursor.close()
            return redirect(url_for('tambah_manufacture'))

        # Jika validasi lolos, masukkan data ke database
        try:
            cursor.execute(
                "INSERT INTO manufacture (manu_id, manu_name, manu_country) VALUES (:manu_id, :manu_name, :manu_country)",
                {"manu_id": manu_id, "manu_name": manu_name, "manu_country": manu_country}
            )
            conn.commit()
            flash("Manufacture berhasil ditambahkan", "success")
        except cx_Oracle.DatabaseError as e:
            flash(f"Gagal menambahkan manufacture: {str(e)}", "danger")
        finally:
            cursor.close()

        return redirect(url_for('master_manufacture'))  # Arahkan ke halaman master manufacture setelah tambah

    # Jika method GET, tampilkan halaman tambah manufacture
    return render_template('tambah_manufacture.html')

    # Route untuk edit manufacture
@app.route('/edit_manufacture/<manu_id>', methods=['GET', 'POST'])
def edit_manufacture(manu_id):
    cursor = conn.cursor()

    if request.method == 'POST':
        # Ambil data dari form
        manu_name = request.form['manu_name']
        manu_country = request.form['manu_country']

        try:
            # Update data manufacture
            cursor.execute(
                "UPDATE manufacture SET manu_name = :manu_name, manu_country = :manu_country WHERE manu_id = :manu_id",
                {"manu_name": manu_name, "manu_country": manu_country, "manu_id": manu_id}
            )
            conn.commit()
            flash("manufacture berhasil diperbarui", "success")
        except cx_Oracle.DatabaseError as e:
            flash(f"Gagal memperbarui manufacture: {str(e)}", "danger")
        finally:
            cursor.close()

        return redirect(url_for('master_manufacture'))  # Redirect ke halaman master_manufacture setelah update

    # Ambil data lokasi berdasarkan manu_id
    cursor.execute("SELECT manu_id, manu_name, manu_country FROM manufacture WHERE manu_id = :manu_id", {"manu_id": manu_id})
    manufacture = cursor.fetchone()
    cursor.close()

    if manufacture:
        manu_data = {"manu_id": manufacture[0], "manu_name": manufacture[1], "manu_country": manufacture[2]}
        return render_template('edit_manufacture.html', manufacture=manu_data)
    else:
        flash("manufacture tidak ditemukan", "danger")
        return redirect(url_for('master_manufacture'))

# Route untuk hapus manufacture
@app.route('/delete_manufacture/<manu_id>', methods=['GET'])
def delete_manufacture(manu_id):
    cursor = conn.cursor()

    try:
        # Hapus lokasi berdasarkan manu_id
        cursor.execute("DELETE FROM manufacture WHERE manu_id = :manu_id", {"manu_id": manu_id})
        conn.commit()
        flash("manufacture berhasil dihapus", "success")
    except cx_Oracle.DatabaseError as e:
        flash(f"Gagal menghapus manufacture: {str(e)}", "danger")
    finally:
        cursor.close()

    return redirect(url_for('master_manufacture'))  # Redirect kembali ke halaman master__manufacture


# Route Master Product-----------------------------------------------------------------------------------------------------------------
@app.route('/master_product')
def master_product():
    search_query = request.args.get('search', '')  # Ambil query pencarian dari input
    cursor = conn.cursor()

    base_query = """
        SELECT a.product_id,
               a.product_name,
               b.type_name,
               c.manu_name,
               d.supp_name,
               e.unit_name,
               f.location_name,
               a.safety_level
        FROM product a
        JOIN product_type b ON a.type_id = b.type_id
        JOIN manufacture c ON a.manu_id = c.manu_id
        JOIN supplier d ON a.supplier_id = d.supplier_id
        JOIN unit e ON a.unit_id = e.unit_id
        JOIN location f ON a.location_id = f.location_id
    """

    if search_query:
        search_condition = """
            WHERE LOWER(a.product_name) LIKE :search_query
            OR LOWER(b.type_name) LIKE :search_query
            OR LOWER(c.manu_name) LIKE :search_query
            OR LOWER(d.supp_name) LIKE :search_query
        """
        full_query = base_query + search_condition + " ORDER BY a.product_name ASC"
        cursor.execute(full_query, {
            "search_query": f"%{search_query.lower()}%"
        })
    else:
        full_query = base_query + " ORDER BY a.product_name ASC"
        cursor.execute(full_query)

    products = [{
        "product_id": row[0],
        "product_name": row[1],
        "type_name": row[2],
        "manu_name": row[3],
        "supp_name": row[4],
        "unit_name": row[5],
        "location_name": row[6],
        "safety_level": row[7]
    } for row in cursor.fetchall()]

    cursor.close()

    return render_template('master_product.html', products=products)

#Route tambah product
@app.route('/tambah_product', methods=['GET', 'POST'])
def tambah_product():
    cursor = conn.cursor()

    #Dropdown manufacture
    cursor.execute("SELECT manu_id, manu_name FROM manufacture")
    manufactures = cursor.fetchall()

    #Dropdown supplier
    cursor.execute("SELECT supplier_id, supp_name FROM supplier")
    suppliers = cursor.fetchall()

    #Dropdown Unit
    cursor.execute("SELECT unit_id, unit_name FROM unit")
    units = cursor.fetchall()

    #Dropdown location
    cursor.execute("SELECT location_id, location_name FROM location where location_type='Warehouse'")
    locations = cursor.fetchall()

    #Dropdown type
    cursor.execute("SELECT type_id, type_name FROM product_type")
    types = cursor.fetchall()

    cursor.close()

    if request.method == 'POST':
        product_name = request.form.get('product_name')
        type_id = request.form.get('type_dropdown')
        manu_id = request.form.get('manu_dropdown')
        supplier_id = request.form.get('supplier_dropdown')
        unit_id = request.form.get('unit_dropdown')
        location_id = request.form.get('location_dropdown')
        safety_level = request.form.get('safety_level')

        # Check if any required field is None (indicating a missing selection)
        if None in (product_name, type_id, manu_id, supplier_id, unit_id, location_id, safety_level):
            flash("Please fill in all fields.", "danger")
            return redirect(url_for('tambah_product'))  # Redirect back to the form

        cursor = conn.cursor()

        # Step 1: Fetch the last product_id for the given type_id
        cursor.execute("""
                        SELECT product_id FROM (
                            SELECT product_id FROM product
                            WHERE product_id LIKE :type_prefix
                            ORDER BY product_id DESC
                        ) WHERE ROWNUM = 1
                    """, {'type_prefix': f"{type_id}%"})

        last_product_id = cursor.fetchone()

        # Step 2: Generate the new product_id
        if last_product_id is not None:
            last_id = last_product_id[0]
            # Extract the numeric part and increment it
            numeric_part = int(last_id[2:])  # Assuming product_id format is like RG0001
            new_numeric_part = numeric_part + 1
        else:
            new_numeric_part = 1  # Start from 1 if no previous id exists

        # Format the new product_id
        new_product_id = f"{type_id}{new_numeric_part:04d}"  # e.g., RG0001, BH0001, OT0001

        # Step 3: Insert the new product with the generated product_id
        cursor.execute("""
            INSERT INTO product (product_id, product_name, type_id, manu_id, supplier_id, unit_id, location_id, safety_level)
            VALUES (:product_id, :product_name, :type_id, :manu_id, :supplier_id, :unit_id, :location_id, :safety_level)
        """, {
            "product_id": new_product_id,
            "product_name": product_name,
            "type_id": type_id,
            "manu_id": manu_id,
            "supplier_id": supplier_id,
            "unit_id": unit_id,
            "location_id": location_id,
            "safety_level": safety_level
        })

        conn.commit()
        cursor.close()

        return redirect(url_for('master_product'))

    return render_template('tambah_product.html',
                           manufactures=manufactures,
                           suppliers=suppliers,
                           units=units,
                           locations=locations,
                           types=types)  # Halaman untuk menambah produk


@app.route('/edit_product/<product_id>', methods=['GET', 'POST'])
def edit_product(product_id):
    cursor = conn.cursor()

    if request.method == 'POST':
        product_name = request.form.get('product_name')
        type_id = request.form.get('type_id')
        manu_id = request.form.get('manu_id')
        supplier_id = request.form.get('supplier_id')
        unit_id = request.form.get('unit_id')
        location_id = request.form.get('location_id')
        safety_level = request.form.get('safety_level')

        cursor.execute("""
            UPDATE product
            SET product_name = :product_name,
                type_id = :type_id,
                manu_id = :manu_id,
                supplier_id = :supplier_id,
                unit_id = :unit_id,
                location_id = :location_id,
                safety_level = :safety_level
            WHERE product_id = :product_id
        """, {
            "product_name": product_name,
            "type_id": type_id,
            "manu_id": manu_id,
            "supplier_id": supplier_id,
            "unit_id": unit_id,
            "location_id": location_id,
            "safety_level": safety_level,
            "product_id": product_id
        })
        conn.commit()
        cursor.close()

        return redirect(url_for('master_product'))

    # Fetch product data based on product_id
    cursor.execute("SELECT * FROM product WHERE product_id = :product_id", {"product_id": product_id})
    product = cursor.fetchone()

    # Fetch options for dropdowns
    cursor.execute("SELECT type_id, type_name FROM product_type")  # Adjust query as necessary
    types = cursor.fetchall()

    cursor.execute("SELECT manu_id, manu_name FROM manufacture")  # Adjust query as necessary
    manufactures = cursor.fetchall()

    cursor.execute("SELECT supplier_id, supp_name FROM supplier")  # Adjust query as necessary
    suppliers = cursor.fetchall()

    cursor.execute("SELECT unit_id, unit_name FROM unit")  # Adjust query as necessary
    units = cursor.fetchall()

    cursor.execute("SELECT location_id, location_name FROM location where location_type='Warehouse'")
    locations = cursor.fetchall()

    cursor.close()

    return render_template('edit_product.html', product=product, types=types, manufactures=manufactures, suppliers=suppliers, units=units, locations=locations)

# Route Delete product
@app.route('/delete_product/<product_id>', methods=['POST'])  # Change to POST
def delete_product(product_id):
    cursor = conn.cursor()

    try:
        # Hapus product berdasarkan product_id
        cursor.execute("DELETE FROM product WHERE product_id = :product_id", {"product_id": product_id})  # Correct binding
        conn.commit()
        flash("Product berhasil dihapus", "success")
    except cx_Oracle.DatabaseError as e:
        flash(f"Gagal menghapus product: {str(e)}", "danger")
    finally:
        cursor.close()

    return redirect(url_for('master_product'))  # Redirect kembali ke halaman product




# Route Master Location-----------------------------------------------------------------------------------------------------------------
@app.route('/master_location')
def master_location():
    search_query = request.args.get('search', '')  # Ambil query pencarian dari input
    cursor = conn.cursor()

    if search_query:
        cursor.execute("SELECT location_id, location_name, location_type FROM location WHERE LOWER(location_name) LIKE :search_query", {
            "search_query": f"%{search_query.lower()}%"
        })
    else:
        cursor.execute("SELECT location_id, location_name, location_type FROM location order by location_type desc")

    locations = [{"location_id": row[0], "location_name": row[1], "location_type": row[2]} for row in cursor.fetchall()]
    cursor.close()

    return render_template('master_location.html', locations=locations)


# Route Untuk Tambah Location
@app.route('/tambah_location', methods=['GET', 'POST'])
def tambah_location():
    if request.method == 'POST':
        # Ambil data dari form
        location_id = request.form['location_id']
        location_name = request.form['location_name']
        location_type = request.form['location_type']

        cursor = conn.cursor()
        # Validasi: Cek apakah location_id sudah ada
        cursor.execute("SELECT COUNT(*) FROM location WHERE location_id = :location_id", {"location_id": location_id})
        count = cursor.fetchone()[0]

        if count > 0:
            flash("Location ID sudah ada. Gunakan ID yang lain.", "danger")
            cursor.close()
            return redirect(url_for('tambah_location'))

        # Jika validasi lolos, masukkan data ke database
        try:
            cursor.execute(
                "INSERT INTO location (location_id, location_name, location_type) VALUES (:location_id, :location_name, :location_type)",
                {"location_id": location_id, "location_name": location_name, "location_type": location_type}
            )
            conn.commit()
            flash("Location berhasil ditambahkan", "success")
        except cx_Oracle.DatabaseError as e:
            flash(f"Gagal menambahkan location: {str(e)}", "danger")
        finally:
            cursor.close()

        return redirect(url_for('master_location'))  # Arahkan ke halaman master location setelah tambah

    # Jika method GET, tampilkan halaman tambah location
    return render_template('tambah_location.html')

# Route untuk edit Location
@app.route('/edit_location/<location_id>', methods=['GET', 'POST'])
def edit_location(location_id):
    cursor = conn.cursor()

    if request.method == 'POST':
        # Ambil data dari form
        location_name = request.form['location_name']
        location_type = request.form['location_type']

        try:
            # Update data lokasi
            cursor.execute(
                "UPDATE location SET location_name = :location_name, location_type = :location_type WHERE location_id = :location_id",
                {"location_name": location_name, "location_type": location_type, "location_id": location_id}
            )
            conn.commit()
            flash("Location berhasil diperbarui", "success")
        except cx_Oracle.DatabaseError as e:
            flash(f"Gagal memperbarui location: {str(e)}", "danger")
        finally:
            cursor.close()

        return redirect(url_for('master_location'))  # Redirect ke halaman master_location setelah update

    # Ambil data lokasi berdasarkan location_id
    cursor.execute("SELECT location_id, location_name, location_type FROM location WHERE location_id = :location_id", {"location_id": location_id})
    location = cursor.fetchone()
    cursor.close()

    if location:
        location_data = {"location_id": location[0], "location_name": location[1], "location_type": location[2]}
        return render_template('edit_location.html', location=location_data)
    else:
        flash("Location tidak ditemukan", "danger")
        return redirect(url_for('master_location'))

# Route untuk hapus Location
@app.route('/delete_location/<location_id>', methods=['GET'])
def delete_location(location_id):
    cursor = conn.cursor()

    try:
        # Hapus lokasi berdasarkan location_id
        cursor.execute("DELETE FROM location WHERE location_id = :location_id", {"location_id": location_id})
        conn.commit()
        flash("Location berhasil dihapus", "success")
    except cx_Oracle.DatabaseError as e:
        flash(f"Gagal menghapus location: {str(e)}", "danger")
    finally:
        cursor.close()

    return redirect(url_for('master_location'))  # Redirect kembali ke halaman master_location


# Route Master Unit------------------------------------------------------------------------------------------------------------------------        
@app.route('/master_unit')
def master_unit():
    search_query = request.args.get('search', '')  # Ambil query pencarian dari input
    cursor = conn.cursor()

    if search_query:
        cursor.execute("SELECT unit_id, unit_name FROM unit WHERE LOWER(unit_name) LIKE :search_query", {
            "search_query": f"%{search_query.lower()}%"
        })
    else:
        cursor.execute("SELECT unit_id, unit_name FROM unit")

    units = [{"unit_id": row[0], "unit_name": row[1]} for row in cursor.fetchall()]
    cursor.close()

    return render_template('master_unit.html', units=units)

# Route untuk Tambah Unit
@app.route('/tambah_unit', methods=['GET', 'POST'])
def tambah_unit():
    if request.method == 'POST':
        # Ambil data dari form
        unit_id = request.form['unit_id']
        unit_name = request.form['unit_name']

        # Simpan data ke database
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO unit (unit_id, unit_name) VALUES (:1, :2)",
            (unit_id, unit_name)
        )
        conn.commit()
        cursor.close()

        # Redirect kembali ke halaman master unit
        return redirect(url_for('master_unit'))

    else:
        # Generate unit_id otomatis
        cursor = conn.cursor()
        cursor.execute("SELECT MAX(unit_id) FROM unit WHERE unit_id LIKE 'U%'")
        result = cursor.fetchone()[0]
        cursor.close()

        # Tentukan unit_id berikutnya
        if result:
            last_number = int(result[1:])  # Ambil angka setelah 'U'
            next_number = last_number + 1
        else:
            next_number = 1  # Jika tidak ada data, mulai dari 1

        unit_id = f"U{next_number:04}"  # Format ID menjadi 'U0001', 'U0002', dst.

        # Tampilkan form tambah unit
        return render_template('tambah_unit.html', unit_id=unit_id)

# Route untuk Edit Unit
@app.route('/edit_unit/<unit_id>', methods=['GET', 'POST'])
def edit_unit(unit_id):
    cursor = conn.cursor()

    if request.method == 'POST':
        unit_name = request.form['unit_name']
        cursor.execute("UPDATE unit SET unit_name = :unit_name WHERE unit_id = :unit_id", {
            "unit_name": unit_name,
            "unit_id": unit_id
        })
        conn.commit()
        cursor.close()

        flash("Unit berhasil diperbarui", "success")
        return redirect(url_for('master_unit'))

    cursor.execute("SELECT unit_id, unit_name FROM unit WHERE unit_id = :unit_id", {"unit_id": unit_id})
    unit = cursor.fetchone()
    cursor.close()

    return render_template('edit_unit.html', unit={"unit_id": unit[0], "unit_name": unit[1]})

# Route untuk Hapus Unit
@app.route('/delete_unit/<unit_id>')
def delete_unit(unit_id):
    try:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM unit WHERE unit_id = :unit_id", {"unit_id": unit_id})
        conn.commit()
        cursor.close()
        flash("Unit berhasil dihapus", "success")
    except cx_Oracle.DatabaseError as e:
        flash(f"Gagal menghapus unit: {str(e)}", "danger")

    return redirect(url_for('master_unit'))

# Route Master Inventory-----------------------------------------------------------------------------------------------------------------
@app.route('/inventory_data')
def inventory_data():
    cursor = conn.cursor()

    base_query = """
        WITH stock_out_agg AS (
            SELECT
                product_id,
                SUM(stock_out_qty) AS total_stock_out
            FROM
                stock_out
            GROUP BY
                product_id
        ),
        stock_in_agg AS (
            SELECT
                product_id,
                SUM(stock_in_qty) AS total_stock_in
            FROM
                stock_in
            GROUP BY
                product_id
        )
        SELECT
            p.product_id,
            p.product_name,
            s.supp_name,
            m.manu_name,
            COALESCE(si.total_stock_in, 0) AS stock_in,
            COALESCE(so.total_stock_out, 0) AS stock_out,
            COALESCE(si.total_stock_in, 0) - COALESCE(so.total_stock_out, 0) AS current_stock,
            p.safety_level
        FROM
            product p
        LEFT JOIN
            supplier s ON p.supplier_id = s.supplier_id
        LEFT JOIN
            manufacture m ON p.manu_id = m.manu_id
        LEFT JOIN
            stock_in_agg si ON p.product_id = si.product_id
        LEFT JOIN
            stock_out_agg so ON p.product_id = so.product_id
        ORDER BY
            p.product_name ASC

    """

    # Execute the query without any search condition
    cursor.execute(base_query)

    # Fetch all rows from the executed query
    rows = cursor.fetchall()

    # Debugging: Log the number of results
    print(f"Number of rows returned: {len(rows)}")  # Log the number of rows returned

    # Create a list of dictionaries from the fetched rows
    inventorys = [{
        "product_id": row[0],
        "product_name": row[1],
        "supp_name": row[2],
        "manu_name": row[3],
        "stock_in": row[4],
        "stock_out": row[5],
        "current_stock": row[6],
        "safety_level": row[7]
    } for row in rows]

    cursor.close()
    print(inventorys)

    return render_template('inventory_data.html', inventorys=inventorys)


if __name__ == "__main__":
    #app.run(debug=True)
    app.run(host='RTS', port=5017, debug=True)
import os
import datetime
from flask import Flask, request, jsonify
from supabase import create_client, Client

# Ambil kredensial dari Environment Variables (lebih aman untuk deployment)
supabase_url = os.environ.get("SUPABASE_URL")
supabase_key = os.environ.get("SUPABASE_KEY")

# Inisialisasi koneksi ke Supabase
supabase: Client = create_client(supabase_url, supabase_key)

app = Flask(__name__)

@app.route('/validate', methods=['POST'])
def validate_license():
    # Ambil kunci dari request yang dikirim aplikasi desktop
    data = request.get_json()
    key_to_check = data.get('license_key')

    if not key_to_check:
        return jsonify({"valid": False, "message": "Kunci lisensi tidak disediakan."}), 400

    try:
        # Cari kunci di tabel 'licenses'
        response = supabase.table('licenses').select('*').eq('license_key', key_to_check).execute()

        # Jika data ditemukan (kunci ada di database)
        if response.data:
            license_info = response.data[0]
            expiry_date_str = license_info.get('expiry_date')

            # Ubah string tanggal menjadi objek date untuk perbandingan
            expiry_date = datetime.datetime.strptime(expiry_date_str, '%Y-%m-%d').date()

            # Bandingkan dengan tanggal hari ini
            if datetime.date.today() <= expiry_date:
                # Lisensi valid dan belum kedaluwarsa
                return jsonify({
                    "valid": True, 
                    "message": f"Lisensi aktif hingga {expiry_date.strftime('%d %B %Y')}"
                })
            else:
                # Lisensi ditemukan tapi sudah kedaluwarsa
                return jsonify({
                    "valid": False, 
                    "message": f"Lisensi sudah kedaluwarsa pada {expiry_date.strftime('%d %B %Y')}"
                }), 403
        else:
            # Kunci tidak ditemukan di database
            return jsonify({"valid": False, "message": "Kunci lisensi tidak valid."}), 404

    except Exception as e:
        print(f"Error saat validasi: {e}")
        return jsonify({"valid": False, "message": "Terjadi error di server."}), 500

# Endpoint untuk memastikan server berjalan
@app.route('/', methods=['GET'])
def index():
    return "License Server is running."
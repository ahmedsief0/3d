from flask import Flask, request, jsonify
import trimesh
import os
import tempfile
import requests

# 
# 1️⃣ FIX-1: لازم 2 underscores هنا
# 
app = Flask(__name__)

@app.route("/")
def home():
    return jsonify({"message": "Trimesh JSON API is running!"})

@app.route("/calculate-area", methods=["POST"])
def calculate_area():
    try:
        data = request.get_json()

        # اتأكد إن JSON وصل
        if not data:
            return jsonify({"error": "No JSON body found"}), 400

        #
        # 2️⃣ FIX-2: ده السطر الصح عشان توصل للينك جوه الـ JSON
        #
        model_url = data.get("result", {}).get("pbr_model", {}).get("url")
        
        if not model_url:
            return jsonify({"error": "Model URL not found in JSON path: result.pbr_model.url"}), 400
        
        # اتأكد إن اللينك ده string مش dictionary
        if not isinstance(model_url, str):
             return jsonify({"error": f"Expected URL to be a string, but got {type(model_url)}"}), 400

        # نزّل الملف مؤقتاً
        response = requests.get(model_url)
        response.raise_for_status() # هيعمل ايرور لو اللينك مش شغال

        temp_dir = tempfile.gettempdir()
        # هنحفظه بنفس الامتداد بتاعه (e.g., .glb)
        file_ext = os.path.splitext(model_url.split('?')[0])[-1]
        filepath = os.path.join(temp_dir, f"temp_model{file_ext}")

        with open(filepath, "wb") as f:
            f.write(response.content)

        # حمّل الموديل واحسب المساحة
        mesh = trimesh.load_mesh(filepath)
        surface_area = mesh.area

        # امسح الملف
        os.remove(filepath)

        return jsonify({
            "status": "success",
            "model_url": model_url,
            "surface_area": surface_area
        })

    except requests.exceptions.RequestException as e:
        # لو فشل في تحميل اللينك
        return jsonify({"error": f"Failed to download model: {str(e)}"}), 500
    except Exception as e:
        # لو فشل في أي حاجة تانية (زي trimesh)
        if 'filepath' in locals() and os.path.exists(filepath):
            os.remove(filepath) # امسح الملف المؤقت لو حصل ايرور
        return jsonify({"error": f"An internal error occurred: {str(e)}"}), 500


#
# 3️⃣ FIX-3: لازم 2 underscores هنا برضو
#
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)

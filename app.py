from flask import Flask, request, jsonify
import trimesh
import os
import tempfile
import requests

app = Flask(_name_)

@app.route("/")
def home():
    return jsonify({"message": "Trimesh JSON API is running!"})

@app.route("/calculate-area", methods=["POST"])
def calculate_area():
    try:
        data = request.get_json()

        # ✅ اتأكد إن JSON وصل
        if not data:
            return jsonify({"error": "No JSON body found"}), 400

        # ✅ استخرج اللينك من JSON
        model_url = data.get("result", {}).get("pbr_model", {}).get("url")
        if not model_url:
            return jsonify({"error": "Model URL not found in JSON"}), 400

        # ✅ نزّل الملف مؤقتاً
        response = requests.get(model_url)
        if response.status_code != 200:
            return jsonify({"error": f"Failed to download model: {response.status_code}"}), 400

        temp_dir = tempfile.gettempdir()
        filepath = os.path.join(temp_dir, "model.glb")

        with open(filepath, "wb") as f:
            f.write(response.content)

        # ✅ حمّل الموديل واحسب المساحة
        mesh = trimesh.load_mesh(filepath)
        surface_area = mesh.area

        # ✅ امسح الملف
        os.remove(filepath)

        return jsonify({
            "status": "success",
            "model_url": model_url,
            "surface_area": surface_area
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)


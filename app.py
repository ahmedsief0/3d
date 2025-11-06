from flask import Flask, request, jsonify
import trimesh
import os
import tempfile
import requests
import numpy # Trimesh يستخدمها

app = Flask(__name__)

@app.route("/")
def home():
    return jsonify({"message": "Trimesh API (with Scaling) is running!"})

@app.route("/calculate-area", methods=["POST"])
def calculate_area():
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "No JSON body found"}), 400

        # --- 1. استخراج رابط الموديل (زي ما هو) ---
        model_url = data.get("result", {}).get("pbr_model", {}).get("url")
        if not model_url or not isinstance(model_url, str):
            return jsonify({"error": "Model URL (result.pbr_model.url) must be a string"}), 400

        # --- 2. استخراج معلومات التحجيم (الجزء الجديد) ---
        scale_info = data.get("scale_info")
        target_dimension = None
        target_value = None

        if scale_info and isinstance(scale_info, dict):
            target_dimension = scale_info.get("dimension") # "height", "width", "depth"
            target_value = scale_info.get("value")       # e.g., 20.0 (المقاس بالسنتيمتر مثلاً)

            # نتأكد إن البيانات سليمة
            if not (target_dimension in ["height", "width", "depth"] and 
                    isinstance(target_value, (int, float)) and 
                    target_value > 0):
                return jsonify({"error": "Invalid scale_info. Use {'dimension': 'height'/'width'/'depth', 'value': > 0}"}), 400

        # --- 3. تحميل الموديل (زي ما هو) ---
        response = requests.get(model_url)
        response.raise_for_status()

        temp_dir = tempfile.gettempdir()
        file_ext = os.path.splitext(model_url.split('?')[0])[-1]
        filepath = os.path.join(temp_dir, f"temp_model{file_ext}")
        with open(filepath, "wb") as f:
            f.write(response.content)

        # --- 4. تحميل الموديل بـ Trimesh (زي ما هو) ---
        mesh = trimesh.load_mesh(filepath)
        
        # حفظ الأبعاد الأصلية للمقارنة
        original_extents = mesh.extents.copy() # [width, depth, height]

        # --- 5. تطبيق التحجيم (المنطق الجديد) ---
        scale_factor = 1.0
        if target_dimension:
            # .extents بتجيب المقاسات [العرض X, العمق Y, الارتفاع Z]
            current_extents = mesh.extents
            
            if target_dimension == "width":    # X-axis
                current_dim = current_extents[0]
            elif target_dimension == "depth":  # Y-axis
                current_dim = current_extents[1]
            elif target_dimension == "height": # Z-axis
                current_dim = current_extents[2]
            
            if current_dim == 0:
                return jsonify({"error": "Cannot scale model with zero dimension"}), 400
            
            # حساب معامل التكبير/التصغير
            scale_factor = target_value / current_dim
            
            # تطبيق التحجيم على كل المحاور (عشان نحافظ على النسبة والتناسب)
            mesh.apply_scale(scale_factor)
        
        # الأبعاد الجديدة بعد التحجيم
        scaled_extents = mesh.extents.copy()

        # --- 6. حساب المساحة (للموديل المُعدل) ---
        surface_area = mesh.area

        # --- 7. مسح الملف المؤقت (زي ما هو) ---
        os.remove(filepath)

        # --- 8. إرجاع النتيجة الكاملة ---
        return jsonify({
            "status": "success",
            "model_url": model_url,
            "scaling": {
                "applied": bool(target_dimension),
                "target_dimension": target_dimension,
                "target_value": target_value,
                "scale_factor_applied": scale_factor
            },
            "original_dimensions_W_D_H": original_extents.tolist(),
            "scaled_dimensions_W_D_H": scaled_extents.tolist(),
            "surface_area_of_scaled_model": surface_area
        })

    except Exception as e:
        if 'filepath' in locals() and os.path.exists(filepath):
            os.remove(filepath)
        return jsonify({"error": f"An internal error occurred: {str(e)}"}), 500

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)

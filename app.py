from flask import Flask, request, jsonify
import trimesh
import os
import tempfile

app = Flask(__name__)

@app.route("/")
def home():
    return "Trimesh Area Calculator API is running!"

@app.route('/calculate-area', methods=['POST'])
def calculate_area():
    # 1. اتأكد إن فيه ملف اترفع
    if 'file' not in request.files:
        return jsonify({"error": "No file part"}), 400
    
    file = request.files['file']
    
    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400

    if file:
        # 2. احفظ الملف بشكل مؤقت
        # بنستخدم tempfile عشان الأمان وإنه يتمسح لوحده
        temp_dir = tempfile.gettempdir()
        filepath = os.path.join(temp_dir, file.filename)
        file.save(filepath)
        
        try:
            # 3. حمّل الموديل بـ trimesh
            mesh = trimesh.load_mesh(filepath)
            
            # 4. احسب المساحة (السطر السحري)
            surface_area = mesh.area
            
            # 5. امسح الملف المؤقت
            os.remove(filepath)
            
            # 6. ارجع النتيجة كـ JSON
            return jsonify({
                "status": "success",
                "filename": file.filename,
                "surface_area": surface_area
            })
        except Exception as e:
            # لو حصل إيرور (مثلاً الملف بايظ)
            if os.path.exists(filepath):
                os.remove(filepath)
            return jsonify({"error": f"Could not process file: {str(e)}"}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
import streamlit.web.cli as stcli
import sys
import os

if __name__ == "__main__":
    # Trỏ đường dẫn tuyệt đối để chạy file app.py chuẩn xác khi đóng gói exe
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    sys.argv = ["streamlit", "run", "app.py", "--global.developmentMode=false"]
    sys.exit(stcli.main())
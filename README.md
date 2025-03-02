# Django Cocktail Management System

A **Django-based web application** for viewing, managing, and organizing cocktails.

## Features:
- **Guests**: Can view **classic cocktails** only.
- **Users**:
  - Can view **classic cocktails** and **public bartender lists**.
  - Can **add classic cocktails** or public ones **to their favorite list**.
- **Bartenders**:
  - Can view and **customize classic cocktails**.
  - Can **create new cocktails**.
  - Can **manage multiple cocktail lists** (public & private).
- **PDF Export**: Every cocktail **can be downloaded as a PDF**.

## Installation:
1. Clone the repository:
   git clone <your-repository-url>
2. Navigate to the project directory:
   cd <project-folder>
3. Create a virtual environment and activate it:
  python -m venv venv source venv/bin/activate # On Windows use: venv\Scripts\activate
4. Install dependencies:
   pip install -r requirements.txt
5. Apply database migrations:
   python manage.py migrate
6. Create a superuser (optional, for Django Admin):
   python manage.py createsuperuser
7. Run the development server:
   python manage.py runserver

## Usage:
- Open **http://127.0.0.1:8000/** in your browser.
- **Login/Register** to access features based on your user role.
- **Explore and manage cocktails!** 🍹

## License:
This project is open-source and available under the **MIT License**.

---

### **🎯 Why This is Better**
✅ **Clear project description**  
✅ **Lists features for different user roles**  
✅ **Includes installation steps for easy setup**  
✅ **Provides instructions on how to run the project**  

🚀 **Now your README is structured and ready for GitHub!** 🎉 Let me know if you need modifications!

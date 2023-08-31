from a11yGPT_package import app, db
from a11yGPT_package.models import User, MonthlySpend
from a11yGPT_package.utils import populate_sample_data

# Call the function to populate sample data
with app.app_context():
    populate_sample_data()

# Run the app
if __name__ == '__main__':
    app.run(debug=True)
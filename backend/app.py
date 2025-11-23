
"""
Car Showroom API Backend
A Flask-based REST API for managing car inventory and test drive bookings
Production-ready with error handling and JSON file storage
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
from datetime import datetime
import json
import os
from pathlib import Path

# Initialize Flask app
app = Flask(__name__)
CORS(app)

# Configuration
DATA_DIR = Path('data')
DATA_DIR.mkdir(exist_ok=True)

CARS_FILE = DATA_DIR / 'cars.json'
BOOKINGS_FILE = DATA_DIR / 'bookings.json'
BRANDS_FILE = DATA_DIR / 'brands.json'

# ==================== UTILITY FUNCTIONS ====================

def load_json_file(filepath, default_data=None):
    """Load JSON data from file with error handling"""
    try:
        if filepath.exists():
            with open(filepath, 'r', encoding='utf-8') as f:
                return json.load(f)
    except (json.JSONDecodeError, IOError) as e:
        print(f"Error loading {filepath}: {e}")
    return default_data or {}

def save_json_file(filepath, data):
    """Save JSON data to file with error handling"""
    try:
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        return True
    except IOError as e:
        print(f"Error saving {filepath}: {e}")
        return False

def validate_booking_data(data):
    """Validate booking form data"""
    required_fields = ['name', 'email', 'phone', 'carModel', 'preferredDate', 'preferredTime']
    errors = {}

    for field in required_fields:
        if field not in data or not str(data[field]).strip():
            errors[field] = f"{field} is required"

    # Email validation
    if 'email' in data:
        if '@' not in str(data['email']):
            errors['email'] = "Invalid email format"

    # Phone validation (10 digits)
    if 'phone' in data:
        phone = str(data['phone']).replace('-', '').replace(' ', '')
        if not phone.isdigit() or len(phone) != 10:
            errors['phone'] = "Phone must be 10 digits"

    return errors if errors else None

# ==================== SAMPLE DATA CREATION ====================

def create_sample_data():
    """Create initial sample data files if they don't exist"""

    sample_cars = [
        {
            "id": 1,
            "brand": "Tata Motors",
            "model": "Nexon EV",
            "price": 1450000,
            "segment": "SUV",
            "fuelType": "Electric",
            "transmission": "Automatic",
            "engineCc": 0,
            "powerBhp": 129,
            "torqueNm": 245,
            "mileage": "200-250 Wh/km",
            "fuelTank": 0,
            "seating": 5,
            "features": ["Electric Range: 312-440 km", "Fast Charging", "Climate Control"],
            "images": ["https://via.placeholder.com/400x300?text=Tata+Nexon+EV"]
        },
        {
            "id": 2,
            "brand": "Tata Motors",
            "model": "Punch",
            "price": 549000,
            "segment": "Hatchback",
            "fuelType": "Petrol",
            "transmission": "Manual",
            "engineCc": 1200,
            "powerBhp": 86,
            "torqueNm": 113,
            "mileage": 18,
            "fuelTank": 44,
            "seating": 5,
            "features": ["ABS with EBD", "Dual Airbags", "Power Windows"],
            "images": ["https://via.placeholder.com/400x300?text=Tata+Punch"]
        },
        {
            "id": 3,
            "brand": "Mahindra & Mahindra",
            "model": "XUV700",
            "price": 1210000,
            "segment": "SUV",
            "fuelType": "Petrol",
            "transmission": "Automatic",
            "engineCc": 2000,
            "powerBhp": 197,
            "torqueNm": 380,
            "mileage": 14,
            "fuelTank": 60,
            "seating": 7,
            "features": ["ADAS Technology", "Panoramic Sunroof", "Leather Seats"],
            "images": ["https://via.placeholder.com/400x300?text=Mahindra+XUV700"]
        }
    ]

    sample_bookings = []

    sample_brands = [
        {"id": 1, "name": "Tata Motors", "description": "Indian multinational automotive", "modelCount": 12},
        {"id": 2, "name": "Mahindra & Mahindra", "description": "Leading utility vehicle manufacturer", "modelCount": 8},
        {"id": 3, "name": "Maruti Suzuki", "description": "India's largest car manufacturer", "modelCount": 15}
    ]

    if not CARS_FILE.exists():
        save_json_file(CARS_FILE, sample_cars)
    if not BOOKINGS_FILE.exists():
        save_json_file(BOOKINGS_FILE, sample_bookings)
    if not BRANDS_FILE.exists():
        save_json_file(BRANDS_FILE, sample_brands)

# ==================== ERROR HANDLERS ====================

@app.errorhandler(404)
def not_found(error):
    """Handle 404 errors"""
    return jsonify({'error': 'Resource not found', 'status': 404}), 404

@app.errorhandler(500)
def internal_error(error):
    """Handle 500 errors"""
    return jsonify({'error': 'Internal server error', 'status': 500}), 500

# ==================== ROUTES ====================

# HEALTH CHECK
@app.route('/api/health', methods=['GET'])
def health_check():
    """API health check endpoint"""
    return jsonify({'status': 'API is running', 'timestamp': datetime.now().isoformat()}), 200

# CARS ENDPOINTS

@app.route('/api/cars', methods=['GET'])
def get_cars():
    """Get all cars with optional filtering"""
    cars = load_json_file(CARS_FILE, [])

    # Apply filters
    brand = request.args.get('brand')
    segment = request.args.get('segment')
    fuel_type = request.args.get('fuelType')
    transmission = request.args.get('transmission')
    min_price = request.args.get('minPrice', type=int)
    max_price = request.args.get('maxPrice', type=int)
    search = request.args.get('search', '').lower()

    filtered_cars = cars

    if brand:
        filtered_cars = [c for c in filtered_cars if c['brand'].lower() == brand.lower()]
    if segment:
        filtered_cars = [c for c in filtered_cars if c['segment'].lower() == segment.lower()]
    if fuel_type:
        filtered_cars = [c for c in filtered_cars if c['fuelType'].lower() == fuel_type.lower()]
    if transmission:
        filtered_cars = [c for c in filtered_cars if c['transmission'].lower() == transmission.lower()]
    if min_price:
        filtered_cars = [c for c in filtered_cars if c['price'] >= min_price]
    if max_price:
        filtered_cars = [c for c in filtered_cars if c['price'] <= max_price]
    if search:
        filtered_cars = [c for c in filtered_cars 
                        if search in c['model'].lower() or search in c['brand'].lower()]

    return jsonify({
        'status': 'success',
        'count': len(filtered_cars),
        'data': filtered_cars
    }), 200

@app.route('/api/cars/<int:car_id>', methods=['GET'])
def get_car(car_id):
    """Get specific car by ID"""
    cars = load_json_file(CARS_FILE, [])
    car = next((c for c in cars if c['id'] == car_id), None)

    if not car:
        return jsonify({'error': f'Car with ID {car_id} not found', 'status': 404}), 404

    return jsonify({'status': 'success', 'data': car}), 200

@app.route('/api/cars', methods=['POST'])
def add_car():
    """Add new car to inventory"""
    data = request.get_json()

    if not data:
        return jsonify({'error': 'No data provided', 'status': 400}), 400

    required_fields = ['brand', 'model', 'price', 'segment', 'fuelType', 'transmission']
    for field in required_fields:
        if field not in data:
            return jsonify({'error': f'Missing required field: {field}', 'status': 400}), 400

    cars = load_json_file(CARS_FILE, [])
    new_id = max([c['id'] for c in cars], default=0) + 1

    new_car = {
        'id': new_id,
        **data,
        'addedDate': datetime.now().isoformat()
    }

    cars.append(new_car)

    if save_json_file(CARS_FILE, cars):
        return jsonify({'status': 'success', 'message': 'Car added', 'data': new_car}), 201
    else:
        return jsonify({'error': 'Failed to save car', 'status': 500}), 500

@app.route('/api/cars/<int:car_id>', methods=['PUT'])
def update_car(car_id):
    """Update existing car"""
    cars = load_json_file(CARS_FILE, [])
    car = next((c for c in cars if c['id'] == car_id), None)

    if not car:
        return jsonify({'error': f'Car with ID {car_id} not found', 'status': 404}), 404

    data = request.get_json()
    if not data:
        return jsonify({'error': 'No data provided', 'status': 400}), 400

    # Update car fields
    for key, value in data.items():
        if key != 'id':  # Don't update ID
            car[key] = value

    car['updatedDate'] = datetime.now().isoformat()

    if save_json_file(CARS_FILE, cars):
        return jsonify({'status': 'success', 'message': 'Car updated', 'data': car}), 200
    else:
        return jsonify({'error': 'Failed to update car', 'status': 500}), 500

@app.route('/api/cars/<int:car_id>', methods=['DELETE'])
def delete_car(car_id):
    """Delete car from inventory"""
    cars = load_json_file(CARS_FILE, [])
    cars = [c for c in cars if c['id'] != car_id]

    if save_json_file(CARS_FILE, cars):
        return jsonify({'status': 'success', 'message': f'Car {car_id} deleted'}), 200
    else:
        return jsonify({'error': 'Failed to delete car', 'status': 500}), 500

# BRANDS ENDPOINTS

@app.route('/api/brands', methods=['GET'])
def get_brands():
    """Get all car brands"""
    brands = load_json_file(BRANDS_FILE, [])
    return jsonify({'status': 'success', 'count': len(brands), 'data': brands}), 200

@app.route('/api/brands/<int:brand_id>', methods=['GET'])
def get_brand(brand_id):
    """Get specific brand"""
    brands = load_json_file(BRANDS_FILE, [])
    brand = next((b for b in brands if b['id'] == brand_id), None)

    if not brand:
        return jsonify({'error': f'Brand with ID {brand_id} not found', 'status': 404}), 404

    return jsonify({'status': 'success', 'data': brand}), 200

# TEST DRIVE BOOKINGS ENDPOINTS

@app.route('/api/bookings', methods=['GET'])
def get_bookings():
    """Get all test drive bookings"""
    bookings = load_json_file(BOOKINGS_FILE, [])
    return jsonify({'status': 'success', 'count': len(bookings), 'data': bookings}), 200

@app.route('/api/bookings', methods=['POST'])
def create_booking():
    """Create new test drive booking"""
    data = request.get_json()

    if not data:
        return jsonify({'error': 'No data provided', 'status': 400}), 400

    # Validate booking data
    errors = validate_booking_data(data)
    if errors:
        return jsonify({'error': 'Validation failed', 'details': errors, 'status': 422}), 422

    bookings = load_json_file(BOOKINGS_FILE, [])
    new_id = max([b.get('id', 0) for b in bookings], default=0) + 1

    new_booking = {
        'id': new_id,
        'name': data['name'].strip(),
        'email': data['email'].strip(),
        'phone': data['phone'].strip(),
        'carModel': data['carModel'],
        'preferredDate': data['preferredDate'],
        'preferredTime': data['preferredTime'],
        'comments': data.get('comments', '').strip(),
        'bookingDate': datetime.now().isoformat(),
        'status': 'pending'
    }

    bookings.append(new_booking)

    if save_json_file(BOOKINGS_FILE, bookings):
        return jsonify({
            'status': 'success',
            'message': 'Test drive booking created successfully',
            'data': new_booking
        }), 201
    else:
        return jsonify({'error': 'Failed to create booking', 'status': 500}), 500

@app.route('/api/bookings/<int:booking_id>', methods=['GET'])
def get_booking(booking_id):
    """Get specific booking"""
    bookings = load_json_file(BOOKINGS_FILE, [])
    booking = next((b for b in bookings if b['id'] == booking_id), None)

    if not booking:
        return jsonify({'error': f'Booking with ID {booking_id} not found', 'status': 404}), 404

    return jsonify({'status': 'success', 'data': booking}), 200

@app.route('/api/bookings/<int:booking_id>', methods=['PUT'])
def update_booking(booking_id):
    """Update booking status"""
    bookings = load_json_file(BOOKINGS_FILE, [])
    booking = next((b for b in bookings if b['id'] == booking_id), None)

    if not booking:
        return jsonify({'error': f'Booking with ID {booking_id} not found', 'status': 404}), 404

    data = request.get_json()
    if 'status' in data:
        booking['status'] = data['status']
    booking['updatedDate'] = datetime.now().isoformat()

    if save_json_file(BOOKINGS_FILE, bookings):
        return jsonify({'status': 'success', 'message': 'Booking updated', 'data': booking}), 200
    else:
        return jsonify({'error': 'Failed to update booking', 'status': 500}), 500

@app.route('/api/bookings/<int:booking_id>', methods=['DELETE'])
def delete_booking(booking_id):
    """Delete booking"""
    bookings = load_json_file(BOOKINGS_FILE, [])
    bookings = [b for b in bookings if b['id'] != booking_id]

    if save_json_file(BOOKINGS_FILE, bookings):
        return jsonify({'status': 'success', 'message': f'Booking {booking_id} deleted'}), 200
    else:
        return jsonify({'error': 'Failed to delete booking', 'status': 500}), 500

# STATISTICS ENDPOINT

@app.route('/api/stats', methods=['GET'])
def get_stats():
    """Get showroom statistics"""
    cars = load_json_file(CARS_FILE, [])
    bookings = load_json_file(BOOKINGS_FILE, [])
    brands = load_json_file(BRANDS_FILE, [])

    stats = {
        'totalCars': len(cars),
        'totalBrands': len(brands),
        'totalBookings': len(bookings),
        'averageCarPrice': sum(c['price'] for c in cars) / len(cars) if cars else 0,
        'brandDistribution': {}
    }

    for car in cars:
        brand = car['brand']
        stats['brandDistribution'][brand] = stats['brandDistribution'].get(brand, 0) + 1

    return jsonify({'status': 'success', 'data': stats}), 200

# ==================== MAIN ====================

if __name__ == '__main__':
    create_sample_data()
    print("\n" + "="*50)
    print("Car Showroom API Server")
    print("="*50)
    print("\nAvailable Endpoints:")
    print("  GET    /api/health            - Health check")
    print("  GET    /api/cars              - Get all cars (with filters)")
    print("  GET    /api/cars/<id>         - Get specific car")
    print("  POST   /api/cars              - Add new car")
    print("  PUT    /api/cars/<id>         - Update car")
    print("  DELETE /api/cars/<id>         - Delete car")
    print("  GET    /api/brands            - Get all brands")
    print("  GET    /api/bookings          - Get all bookings")
    print("  POST   /api/bookings          - Create booking")
    print("  GET    /api/bookings/<id>     - Get booking")
    print("  PUT    /api/bookings/<id>     - Update booking")
    print("  DELETE /api/bookings/<id>     - Delete booking")
    print("  GET    /api/stats             - Get statistics")
    print("\nStarting server on http://localhost:5000")
    print("="*50 + "\n")

    app.run(debug=True, host='0.0.0.0', port=5000)

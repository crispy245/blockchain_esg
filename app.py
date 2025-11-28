"""
Simple Flask App - Reads from YOUR Blockchain Contract
Fill in your contract address and you're done!
"""

from flask import Flask, render_template, redirect, url_for
from web3 import Web3
from datetime import datetime
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

app = Flask(__name__)

# ===== LOAD FROM ENVIRONMENT VARIABLES =====
CONTRACT_ADDRESS = os.getenv('CONTRACT_ADDRESS')
INFURA_URL = os.getenv('INFURA_URL')


app = Flask(__name__)


# ===== Contract ABI - This tells Python how to talk to your contract =====
CONTRACT_ABI = [
    {
        "inputs": [{"internalType": "string", "name": "_productId", "type": "string"}],
        "name": "getProduct",
        "outputs": [
            {"internalType": "string", "name": "productId", "type": "string"},
            {"internalType": "uint256", "name": "timestamp", "type": "uint256"},
            {"internalType": "string", "name": "totalCarbon", "type": "string"},
            {"internalType": "string", "name": "carbonOffset", "type": "string"}
        ],
        "stateMutability": "view",
        "type": "function"
    },
    {
        "inputs": [{"internalType": "string", "name": "_productId", "type": "string"}],
        "name": "getStageCount",
        "outputs": [{"internalType": "uint256", "name": "", "type": "uint256"}],
        "stateMutability": "view",
        "type": "function"
    },
    {
        "inputs": [
            {"internalType": "string", "name": "_productId", "type": "string"},
            {"internalType": "uint256", "name": "_index", "type": "uint256"}
        ],
        "name": "getStage",
        "outputs": [
            {"internalType": "string", "name": "stage", "type": "string"},
            {"internalType": "string", "name": "location", "type": "string"},
            {"internalType": "string", "name": "verification", "type": "string"},
            {"internalType": "string", "name": "carbonFootprint", "type": "string"},
            {"internalType": "string", "name": "additionalInfo", "type": "string"}
        ],
        "stateMutability": "view",
        "type": "function"
    }
]

# Connect to blockchain
w3 = Web3(Web3.HTTPProvider(INFURA_URL))


def get_real_blockchain_data(product_id):
    """
    Read data from YOUR deployed contract on Sepolia blockchain
    """
    try:
        # Create contract instance
        contract = w3.eth.contract(address=CONTRACT_ADDRESS, abi=CONTRACT_ABI)
        
        # Get product info
        product = contract.functions.getProduct(product_id).call()
        
        # Get number of stages
        stage_count = contract.functions.getStageCount(product_id).call()
        
        # Get all stages
        stages = []
        for i in range(stage_count):
            stage_data = contract.functions.getStage(product_id, i).call()
            
            # Compute actual hash from stage data
            from eth_utils import keccak
            data_to_hash = ''.join([
                stage_data[0],  # stage
                stage_data[1],  # location
                stage_data[2],  # verification
                stage_data[3],  # carbonFootprint
                stage_data[4]   # additionalInfo
            ])
            actual_hash = '0x' + keccak(text=data_to_hash).hex()
            
            stage_info = {
                'stage': stage_data[0],
                'location': stage_data[1],
                'verification': stage_data[2],
                'carbon_footprint': stage_data[3],
                'hash': actual_hash  # Real hash computed from stage data
            }
            
            # Add renewable energy if it exists
            if stage_data[4]:  # additionalInfo field
                if 'solar' in stage_data[4].lower() or 'renewable' in stage_data[4].lower():
                    stage_info['renewable_energy'] = stage_data[4]
            
            stages.append(stage_info)
        
        # Format timestamp
        timestamp = datetime.fromtimestamp(product[1]).strftime('%Y-%m-%d %H:%M:%S UTC')
        
        return {
            'transaction_hash': CONTRACT_ADDRESS[:10] + '...' + CONTRACT_ADDRESS[-8:],
            'timestamp': timestamp,
            'supply_chain': stages,
            'total_carbon': product[2],
            'carbon_offset': product[3]
        }
    
    except Exception as e:
        print(f"❌ Error reading from blockchain: {e}")
        print(f"   Make sure CONTRACT_ADDRESS is correct!")
        return None


# Static garment info
GARMENTS = {
    'organic-cotton-tshirt': {
        'name': 'Organic Cotton T-Shirt',
        'description': 'A comfortable, breathable t-shirt made from 100% certified organic cotton',
        'image': 'https://images.unsplash.com/photo-1521572163474-6864f9cf17ab?w=800',
        'price': '$45',
        'esg_claims': [
            'Certified Organic Cotton (GOTS)',
            'Carbon-neutral manufacturing',
            'Fair Trade Certified',
            'Water-efficient dyeing process',
            'Recyclable packaging'
        ]
    }
}


@app.route('/')
def home():
    # Redirect directly to the blockchain-verified version
    return redirect(url_for('version_b', garment_id='organic-cotton-tshirt'))


@app.route('/version-a/<garment_id>')
def version_a(garment_id):
    garment = GARMENTS.get(garment_id)
    if not garment:
        return "Garment not found", 404
    return render_template('version_a.html', garment=garment, garment_id=garment_id)


@app.route('/version-b/<garment_id>')
def version_b(garment_id):
    garment = GARMENTS.get(garment_id)
    if not garment:
        return "Garment not found", 404
    
    # Get REAL blockchain data
    blockchain_data = get_real_blockchain_data(garment_id)
    
    if blockchain_data:
        garment['blockchain_data'] = blockchain_data
        garment['etherscan_link'] = f"https://sepolia.etherscan.io/address/{CONTRACT_ADDRESS}"
        print("✅ Successfully loaded blockchain data!")
    else:
        print("❌ Failed to load blockchain data - check your contract address")
        return "Error: Could not load blockchain data. Check console.", 500
    
    return render_template('version_b.html', garment=garment, garment_id=garment_id)


if __name__ == '__main__':
    print("\n" + "="*60)
    print("  BLOCKCHAIN FLASK APP")
    print("="*60)
    
    # Check connection
    if w3.is_connected():
        print("✅ Connected to Sepolia blockchain")
        print(f"📍 Reading from contract: {CONTRACT_ADDRESS}")
        print(f"🔗 View on Etherscan: https://sepolia.etherscan.io/address/{CONTRACT_ADDRESS}")
    else:
        print("❌ Not connected to blockchain")
        print("   Check your internet connection")
    
    print("\n🚀 Starting Flask app on http://localhost:5000")
    print("   Now redirects directly to blockchain-verified organic cotton t-shirt!")
    print("="*60 + "\n")
    
    app.run(debug=True, host='0.0.0.0', port=5000)
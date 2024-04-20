from flask import Flask, request, jsonify
app = Flask(__name__)


def rank():
	'''
	method for ranking
	'''

@app.route('/ranker', methods=['POST'])
def initRank():
	'''

	ranking API
	'''
	params = request.json
	print(params['table_prefix'])
	print(len(params))
	if(len(params) < 2):
		return jsonify("{\'status\':400, \'result\':\'required arguments were not sent\'}")
	else :
		rank()
		#do ranking
	return jsonify("{\'status\': 200, \'result\':\'ranking complete\'}")

if __name__ == '__main__':
    app.run(host='slcam855.us.oracle.com')
from flask import Flask, request, jsonify
app = Flask(__name__)


def rank(table_prefix,run_id):
	# print(t)
	# print (r)
	return run_id
	'''
	method for ranking
	'''

@app.route('/ranker/<table_prefix>/<run_id>', methods=['GET'])
def initRank(table_prefix, run_id):
	res = rank(table_prefix,run_id)
	'''

	ranking API
	'''
	return res
	# return jsonify("{\'status\': 200, \'result\':\'ranking complete\'}")

if __name__ == '__main__':
    app.run(host='adct61vm0009-eoib1.us.oracle.com')

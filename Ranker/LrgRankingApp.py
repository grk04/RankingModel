from flask import Flask, request, jsonify
from LrgRanker import *
import Logutil

app = Flask(__name__)


def call_rank(table_prefix, run_id, label_opt):
    try:
        print ("call ranking ")
        Ranker = LrgRanker(table_prefix, int(run_id), 0)
        Ranker.start_ranking(int(label_opt))
        return "suc"
    except Exception as e:
        return str(e)


@app.route('/ranker/<table_prefix>/<run_id>/<label_opt>', methods=['GET'])
def ranker(table_prefix, run_id, label_opt):

    res = call_rank(table_prefix, run_id, label_opt)
    '''

    ranking API
    '''

    if res == 'suc':
        print("success")
        ret = "{\'status\': 200, \'result\':\'ranking success\'}"
    else:
        ret = "{\'status\': 400, \'result\':\'%s\'}" % res

    return ret


if __name__ == '__main__':
    app.debug = True
    app.run(host='adct61vm0009-eoib1.us.oracle.com', port=8020, threaded=True)


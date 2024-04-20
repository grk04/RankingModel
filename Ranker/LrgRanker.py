 
'''
Base class for Lrg ranking
Transaction and Label implement its functionality

'''

from CoverageDB import *
import logging
import Logutil
import sys
try:
    import cx_Oracle
except ImportError as  ie:
    print(f"Failed to import cx_Oracle {ie}")
    sys.exit(1)
import numpy
import math
import time

logger = None
is_label_run = 0


class LrgRanker:

    def __init__(self, tab_prefix, run_id, print_debug):
        """

        :param tab_prefix:
        :param run_id:
        :param print_debug:
        """
        global logger
        log_file = "/tmp/rank_" + str(run_id) + ".log"
        Logutil.init_logger(log_file)
        logger = Logutil.get_logger()

        logger.log(logging.INFO, "Ranker invoked for run_id = [%d] and table "
                                 "=[%s]" % (run_id, tab_prefix))

        # protected var "single _"
        self._st_time = time.time()
        self._run_id = run_id
        self._tab_prefix = tab_prefix
        self._hit_tab = tab_prefix + "_hit"
        self._rtn_tab = tab_prefix + "_rtn"
        self._tst_tab = tab_prefix + "_tst"
        self._total_rtn = 0
        self._total_lrg = 0

        self._db_lrg_data = {}
        self._db_rtn_data = {}
        self._in_rtn_data = {}

        """
        hit_map array related var's
        hit_map array is 2-D MxN array
        """
        self._hit_map_array = None
        self._lrg_idx_map = {}
        self._rtn_idx_map = {}
        self._rtn_idx = 0
        self._lrg_idx = 0
        self._coveragedb = None
        self._rtn_lrg_map = {}
        self._tst_ids = []

        self._print_debug = print_debug

    def initialize(self):
        """
        init various data
        :return:
        """
        logger.log(logging.DEBUG, "Initialize ranking class")

        try:
            self._coveragedb = CoverageDB()
        except Exception as  e:
            logger.log(logging.ERROR, "Fatal Error in db connection"+str(e))
            return -1

        if self.get_lrg_data_from_db() == -1:
            return -1
        if self.get_input_routine_data() == -1:
            return -1

        logger.log(logging.DEBUG, "Initialize hit_map array of [%d][%d] "
                                  "" % (self._total_rtn, self._total_lrg))

        self._hit_map_array = numpy.zeros([self._total_rtn, self._total_lrg])

        return 0

    def print_debug_data(self, msg):
        """

        :param msg:
        :return:
        """
        if self._print_debug == 0:
            return
        else:
            print (msg)

    def get_lrg_data_from_db(self):
        """
        Fetch db lrg data
        :return:
        """
        s_t = time.time()
        try:
            cursor = self._coveragedb.get_cursor()
        except Exception as e:
            logger.log(logging.ERROR, "DB error in getting cursor " + str(e))
            return -1

        stmt = """select test_id, test_name, NVL(cluster_id, -1) from """ \
               + self._tst_tab + " order by 1"

        logger.log(logging.DEBUG, "Running query = [%s] " % stmt)
        self._db_lrg_data.clear()
        try:
            cursor.execute(stmt)
            for row in cursor.fetchall():
                test_id = row[0]
                test_name = row[1]
                cluster_id = row[2]
                if test_id in self._db_lrg_data:
                    logger.log(logging.DEBUG, "Duplicate lid = [%d]" % test_id)
                    continue

                self._total_lrg += 1
                data = dict()
                data['test_name'] = test_name
                data['cluster_id'] = cluster_id
                data['is_hit'] = 0
                data['score'] = 0
                data['rank'] = -1
                data['total_sum'] = 0
                data['array_idx'] = self._lrg_idx

                self._db_lrg_data[test_id] = data
                # reverse map
                # print("test-id : " +str(test_id))
                # print("test-idx : " + str(self._lrg_idx))
                # self._tst_id_idx_map[test]
                self._lrg_idx_map[self._lrg_idx] = test_id
                self._lrg_idx += 1

            t_e = round(time.time() - s_t, 2)
            logger.log(logging.INFO, "Fetched total lrg  from "
                                     "[%d] [%s] sec elapsed"
                                     "" % (self._total_lrg, str(t_e)))
        except cx_Oracle.Error as dbe:
            logger.log(logging.ERROR, "Fatal Error in getting lrg "
                                      " from db run_id =[%d] (%s)"
                                      "" % (self._run_id, str(dbe)))
            return -1

        finally:
            if cursor:
                cursor.close()

        return 0

    def get_input_routine_data(self):
        """
        get input rtn  data
        :return:
        """
        t_s = time.time()
        logger.log(logging.DEBUG, "Fetch input routine Data from db for "
                                  "run_id = [%d] " % self._run_id)

        stmt = "SELECT routine_id, routine_name, type from pck_rank_input " \
               "where routine_id is not null and run_id = %d" % self._run_id
        logger.log(logging.DEBUG, "Running query = [%s] " % stmt)

        try:
            cursor = self._coveragedb.get_cursor()
        except Exception as  e:
            logger.log(logging.ERROR, "DB error in getting cursor " + str(e))
            return -1
        try:
            cursor.execute(stmt)
            for row in cursor.fetchall():
                rid = row[0]
                r_name = row[1]
                r_type = row[2]
                if rid not in self._in_rtn_data:
                    self._total_rtn += 1
                    self._in_rtn_data[rid] = [r_name, r_type]

                else:
                    prev_type = self._in_rtn_data[rid][1]
                    if prev_type != r_type:  # C!=F or vice versa
                        self._in_rtn_data[rid][1] = 'B'

            t_e = round(time.time() - t_s, 2)
            logger.log(logging.INFO, "Fetched total rtn from [%d] [%s] sec "
                                     "elapsed " % (self._total_rtn, str(t_e)))

        except cx_Oracle.Error as  dbe:
            logger.log(logging.ERROR, "Fatal Error in getting input rtn"
                                      " data from db run_id = [%d] (%s)"
                                      "" % (self._run_id, str(dbe)))
            return -1

        finally:
            if cursor:
                cursor.close()

        return 0

   # ##############  prepare 2-D array based on data ##################### #

    def get_routine_index(self, rid):
        """
        get routine_index for array
        :return:
        """
        if rid not in self._db_rtn_data:

            self._rtn_idx_map[self._rtn_idx] = rid

            data = dict()
            data['array_idx'] = self._rtn_idx
            data['log_value'] = 0
            self._db_rtn_data[rid] = data
            r_idx = self._rtn_idx
            self._rtn_idx += 1
        else:
            r_idx = self._db_rtn_data.get(rid).get('array_idx')

        return r_idx

    def update_hit_map_array(self, rid, hit_map):
        """
        update hit_map_array  for rid a
        :param rid:
        :param hit_map:
        :return:
        """

        lrg_list = []
        hit_map_data = hit_map.split("-")
        for data in hit_map_data:
            tmp = data.split(':')
            w = float(tmp[1])
            lid = int(tmp[0])
            if lid not in self._db_lrg_data:
                logger.log(logging.WARNING, "Data mismatch for [%d]" % lid)
                continue
            # mark that lrg as hit
            self._db_lrg_data[lid]['is_hit'] = 1
            l_idx = self._db_lrg_data.get(lid).get('array_idx')

            r_idx = self.get_routine_index(rid)

            self.print_debug_data("[%d]= > [%d][%d] = %f"
                                  "" % (rid, r_idx, l_idx, w))

            self._hit_map_array[r_idx][l_idx] = w
            if is_label_run != 0: # for label runs
                lrg_list.append(lid)

        self._rtn_lrg_map[rid] = lrg_list

    def get_hit_map_from_db(self):
        """
        get hit map data from db using _hitmap tab
        :return:
        """
        t_s = time.time()
        hitmap_tab = self._tab_prefix + "_hitmap"
        logger.log(logging.DEBUG, "getting hit_map data from " + hitmap_tab)

        stmt = "select a.rid, a.hitmap from " + hitmap_tab + \
               " a, pck_rank_input b where b.run_id =%d" \
               " and  b.routine_id = a.rid" % self._run_id

        logger.log(logging.DEBUG, "Running [%s]" % stmt)

        try:
            cursor = self._coveragedb.get_cursor()
        except Exception as  e:
            logger.log(logging.ERROR, "DB error in getting cursor " + str(e))
            return -1

        try:
            cursor.execute(stmt)
            # cx_Oracle limit for clob data
            for row in cursor:
                rid = row[0]
                hit_map = str(row[1].read())
                self.update_hit_map_array(rid, hit_map)

            t_e = round(time.time() - t_s, 2)
            logger.log(logging.INFO, "Fetched hit_map [%s] sec elapsed"
                                     "" % str(t_e))

        except cx_Oracle.Error as  dbe:
            logger.log(logging.ERROR, "Failed to get Lrg data "
                                      "" + str(dbe))
            return -1

        finally:
            cursor.close()

        return 0

    ######## 2-D map is ready start ranking algorithm here ########

    def update_total_sum_for_lrg(self):
        """
        here we update ts for each lrgs
        :return:
        """
        t_s = time.time()
        logger.log(logging.DEBUG, "Update total denominator"
                                  " sum  for each lrgs ")

        for lid in self._db_lrg_data.keys():  # --range(0, self._total_lrg):
            l_idx = self._db_lrg_data[lid]['array_idx']
            #print "l_idx is:"
            #print l_idx

            total_sum = 0.0
            for w in self._hit_map_array[:, l_idx]:

                total_sum += w
            # print "ts for lrg ", i, ts

            self._db_lrg_data[lid]['total_sum'] = total_sum

        t_e = round(time.time() - t_s, 2)
        logger.log(logging.DEBUG, "updated total sum for lrg "
                                  "[%s] sec elapsed " % str(t_e))

    def update_log_value_for_routine(self):
        """
        update log for all routine
        :return:
        """
        t_s = time.time()
        logger.log(logging.DEBUG, "updating log_value for routines")
        '''
        t = 0
        for lid, v in self._db_lrg_data.iteritems():
            h = v.get('is_hit')
            if int(h) >0:
                 t = t+1
        print t, self._total_lrg
        '''
        for i in range(0, self._total_rtn):
            hit_lrgs = numpy.count_nonzero(self._hit_map_array[i,])
            if hit_lrgs > 0:
                tmp = float(1+self._total_lrg) / float(hit_lrgs)
                log_val = math.log(tmp)

            else:
                log_val = 0

            # get routine_id

            rid = self._rtn_idx_map[i]
            self._db_rtn_data[rid]['log_value'] = log_val

        t_e = round(time.time() - t_s, 2)
        logger.log(logging.DEBUG, "updated log value for routines "
                                  "[%s] sec elapsed " % str(t_e))

    def compute_final_score(self):
        """
        compute final score for lrg
        :return:
        """
        t_s = time.time()
        logger.log(logging.INFO, "compute final score")
        # print(self._db_lrg_data[0])
        for i in range(0, self._total_lrg):
            tid = self._lrg_idx_map[i]
            total_sum = self._db_lrg_data[tid]['total_sum']
            if total_sum == 0:
                continue

            total_weight = 0.0

            j = 0
            for weight in self._hit_map_array[:, i]:
                # get log value
                rid = self._rtn_idx_map[j]
                log_val = self._db_rtn_data[rid]['log_value']
                j += 1
                if log_val == 0:
                    continue

                if self._total_rtn ==1:
                    w = float(weight) #/ float(total_sum)
                else:
                    w = float(weight)/ float(total_sum)
                    #      print "w is :"
                    #     print w
                total_weight = total_weight + w * log_val
                # to rank multiply with large number
                self._db_lrg_data[tid]['score'] = total_weight * 100000

        t_e = round(time.time() - t_s, 2)

        logger.log(logging.DEBUG, "calculated final score "
                                  "[%s] sec elapsed " % str(t_e))

    def apply_round_robin(self):
        """
        apply round round robin algo
        :return:
        """
        t_s = time.time()
        logger.log(logging.INFO, "sorting lrgs based on rank")

        cluster_lrg_map = {}
        total_cluster_score = {}
        for lid in self._db_lrg_data.keys():
            lrg_data = self._db_lrg_data.get(lid)
            is_hit = lrg_data.get('is_hit')
            if is_hit == 0:
                continue

            cid = lrg_data.get('cluster_id')
            score = lrg_data.get('score')
            if cid not in cluster_lrg_map:
                cluster_lrg_map[cid] = [(lid, score)]
                total_cluster_score[cid] = score
            else:
                cluster_lrg_map[cid].append((lid, score))
                total_cluster_score[cid] = total_cluster_score[cid]+score

        # sort data for each cluster

        for cid in cluster_lrg_map:

            lrg_list = cluster_lrg_map.get(cid)
            lrg_list.sort(key=lambda x: x[1], reverse=True)
            cluster_lrg_map[cid] = lrg_list

        # round robin for rank

        rank = 0
        idx = 0
        loop_count = 0
        while True:
            # for cid in cluster_lrg_map.iterkeys():
            for cid, s in sorted(total_cluster_score.items(), key=lambda item: item[1],
                                 reverse=True):
                l_lrg = cluster_lrg_map[cid]
                if len(l_lrg) > idx:
                    rank += 1
                    test_id = l_lrg[idx][0]
                    self._db_lrg_data[test_id]['rank'] = rank

            if rank >= self._total_lrg:
                break
            idx += 1
            loop_count += 1

            # in case of issue avoid infinite loop
            if loop_count > self._total_lrg:
                break

        t_e = round(time.time() - t_s, 2)
        logger.log(logging.DEBUG, "got final rank of lrgs"
                                  "[%s] sec elapsed " % str(t_e))

    def insert_routine_lrg_map(self, rid, lrg_list=[]):
        """
        this is for label option inserting on client side is very slow

        :param rid:
        :param r_name
        :param lrg_list:
        :return:
        """
        r_name = self._in_rtn_data.get(rid)[0]
        logger.log(logging.DEBUG, "Insert data for [%s] in pck_rank_output_label" % r_name)

        try:
            cursor = self._coveragedb.get_cursor()
        except Exception as  e:
            logger.log(logging.ERROR , "DB error in getting "
                                      "cursor "+str(e))
            return -1

        stmt = "insert into PCK_RANK_OUTPUT_LABEL(run_id, routine_id, routine_name," \
               " test_name, cluster_id, rank, score)" \
               " values (:1, :2, :3, :4, :5, :6, :7)"

        in_data = []
        for lid in lrg_list:
            test_name = self._db_lrg_data.get(lid).get('test_name')
            cluster_id = self._db_lrg_data.get(lid).get('cluster_id')
            score = self._db_lrg_data.get(lid).get('score')
            rank = self._db_lrg_data.get(lid).get('rank')
            row = (self._run_id, rid, r_name, test_name, cluster_id, rank, score)
            in_data.append(row)

        try:
            cursor.executemany(stmt, in_data)
        except cx_Oracle.Error as  e:
            logger.log(logging.ERROR, "Failed to insert data for [%s] err = "
                                      "[%s]" % (r_name, str(e)))
            self._coveragedb.rollback()
            return -1
        finally:
            self._coveragedb.commit()
        return 0

    def set_out_for_label(self):
        """
        set PCK_RANK_OUTPUT_LABEL
        """

        logger.log(logging.DEBUG, "Insert data for in pck_rank_output_label")
        rt = 0
        for rid in self._rtn_lrg_map.keys():
            lrg_list = self._rtn_lrg_map.get(rid)
            if self.insert_routine_lrg_map(rid, lrg_list) == -1:
                rt = -1

    def insert_lrg_data_in_db(self):
        """
        insert lrg data in pck_rank_out
        :return:
        """
        t_s = time.time()
        logger.log(logging.INFO, "Insert lrg data in pck_rank_output ")
        try:
            cursor = self._coveragedb.get_cursor()
        except Exception as e:
            logger.log(logging.ERROR, "DB error in getting "
                                      "cursor " + str(e))
            return -1

        insert_data = []
        for lid in self._db_lrg_data.keys():
            test_name = self._db_lrg_data.get(lid).get('test_name')
            cluster_id = self._db_lrg_data.get(lid).get('cluster_id')
            score = self._db_lrg_data.get(lid).get('score')
            rank = self._db_lrg_data.get(lid).get('rank')
            if rank == -1:
                continue
            row = (self._run_id, test_name, cluster_id, score, rank, lid)
            insert_data.append(row)
        sql = "INSERT INTO PCK_RANK_OUTPUT(RUN_ID, TEST_NAME, CLUSTER_ID," \
              " SCORE, RANK, test_id) " \
              "VALUES (:1, :2, :3, :4, :5, :6)"
        try:
            cursor.executemany(sql, insert_data)
        except Exception as  e:
            logger.log(logging.ERROR, "Failed to insert  lrg data for err = [%s]" % str(e))

            self._coveragedb.rollback()
            return -1
        finally:
            self._coveragedb.commit()

        t_e = round(time.time() - t_s, 2)
        logger.log(logging.INFO, "Inserted lrgs data into _out tab "
                                 "[%s] sec elapsed " % str(t_e))
        return 0

    def start_ranking(self, label_run=0):
        """
        main interface method
        :param label_run : set to 1 for label option ...
        :return:
        """
        t_s = time.time()
        logger.log(logging.INFO, "starting ranking of run_id = [%d] "
                                 "[%s]" % (self._run_id, str(t_s)))
        global is_label_run
        is_label_run = label_run
        try:
            if self.initialize() == -1:
                raise Exception("initialize returned -1 status")

        except Exception as e:
            raise Exception("Failed to initialize ranking [%s]" % str(e))

        try:

            if self.get_hit_map_from_db() == -1:
                raise Exception("Failed to get hitMap from db")
        except Exception as e:
            raise Exception("Exception in getting hitmap from db"
                            " [%s]" % str(e))

        try:
            self.update_total_sum_for_lrg()
        except Exception as  e:
            raise Exception("exception in calculating total sum [%s]"
                            "" % str(e))

        try:
            self.update_log_value_for_routine()
        except Exception as  e:
            raise Exception("exception in calculating log value [%s]"
                            "" % str(e))
        try:
            self.compute_final_score()
        except Exception as  e:
            raise Exception("exception in calculating final score [%s]"
                            "" % str(e))

        try:
            self.apply_round_robin()
        except Exception as  e:
            raise Exception("exception in getting final rank [%s]"
                            "" % str(e))

        try:
            if is_label_run == 0:
                if self.insert_lrg_data_in_db() == -1:
                    raise Exception("insert to pck_rank_output"
                                    "  returned -1 status")
            else:
                if self.set_out_for_label() == -1:
                    raise Exception("insert to pck_rank_output_label"
                                    "  returned -1 status")
        except Exception as e:
            raise Exception("exception in inserting data to out tab [%s]"
                            "" % str(e))

        self._coveragedb.close()
        t_e = round(time.time() - t_s, 2)
        logger.log(logging.INFO, "Done ranking [%s] sec elapsed "
                                 "" % str(t_e))


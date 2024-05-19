**Model Description**
Before a transaction is merged, we need to run lrgs to make sure the existing tests are not broken by the code or test changes in the transaction. It is useful for us to know which lrgs are more related with the changes in this transaction so that we could give higher priority to these lrgs and it makes it more efficient to capture potential issues as well.
Here we propose a LRG rank model to help us rank the lrgs based on their connection with the transaction changes.
Suppose we have a total of N lrgs and there are some metric that can be used to measure the connection between an lrg and a file. For example, for a code file, the metric could be the number of times this code file is accessed in an lrg, for a test file, the metric could be the number of times the lrg calls the test. There are other ways to define the metrics as well, let’s assume the metric is now determined and we use aij and bij to denote its value for a code file and a test file respectively. If we have P code files and Q test files, then we can create a matrix as follows:
 	lrg_1	lrg_2	lrg_3	…	…	lrg_(N-1)	lrg_N
cf_1	a11	a12	a13	…	…	a1(N-1)	a1N
cf_2	a21	a22	a23	…	…	a2(N-1)	a2N
… …    	… …    	… …    	… …    		… …    	… …    
cf_(P-1)	a(P-1)1	a(P-1)2	a(P-1)3	…	…	a(P-1)(N-1)	a(P-1)N
cf_P	aP1	aP2	aP3	…	…	aP(N-1)	aPN
 	 	 	 	 	 	 	 
 	 						 
tf_1	b11	b12	b13	…	…	b1(N-1)	b1N
tf_2	b21	b22	b23	…	…	b2(N-1)	b2N
… …    	… …    	… …    	… …    		… …    	… …    
tf_(Q-1)	b(Q-1)1	b(Q-1)2	b(Q-1)3	…	…	b(Q-1)(N-1)	b(Q-1)N
tf_Q	bQ1	bQ2	bQ3	…	…	bQ(N-1)	bQN

Also, let’s assume there is a transaction that modifies the following files: cf_1, cf_3 and tf_4. How do we find the lrgs that are most relevant with these three files?
Actually the problem is quite similar to the ranking of web pages. The files in the transaction are like the key words used in web page search. 
Just like we use the frequency of a key word in a page as a measurement of relevance, similarly, we can use the “frequency” of a file to measure its importance. For example, for lrg_j, it can be measure by a_ij/(∑_(t=1)^P▒a_tj ) for a code file cf_i and b_kj/(∑_(t=1)^P▒a_tj ) for a test file tf_k.
Next, in the web page ranking, we should also consider the importance of a key word itself because different word carries different amount of information. This is measured by log(N/n) where N is the total number of web pages, and n is the number of pages that contains the specific key word. Similarly, to obtain the importance of a file f, we first count the number of lrgs that call it (Nf), and then calculate log(N/Nf). As you can see, if a file is called in every lrg, the importance of this file is log(N/N) = 0, which is expected, as it gives us no information at all about the priority of lrgs with regard to this file. On the other hand, if a file is only called in one lrg, then this file’s importance score is log(N), which implies that this file is very useful in ranking lrgs.
Now, we combine the frequency and the importance of a file to get the lrg score relevant to this file. Take lrg_j for example, for a code file cf_i, its score is a_ij/(∑_(t=1)^P▒a_tj )  •log⁡(N/N_i^c  ) and for a test file tf_k, its score is b_kj/(∑_(t=1)^P▒a_tj )•log⁡(N/N_k^t  ). To get the final lrg score with regard to a transaction, we just need to sum up all the its file scores:
S_j=∑_(i∈CF)▒〖a_ij/(∑_(t=1)^P▒a_tj )  •log⁡(N/(N_i^c )) 〗+λ ∑_(k∈TF)▒〖b_kj/(∑_(t=1)^P▒a_tj )  log⁡(N/(N_k^t )) 〗                       (*)
where CF is the index set for code files in the transaction,  TF is the index set for test files in the transaction, N_i^c is the number of lrgs that call the ith code file,  N_k^t is the number of lrgs that call the kth test file.
As test file and code file may carry different amount of information, we use λ to help tune this model. If  0<λ<1, we put more weights on code file scores, and if λ>1, the model is skewed toward the test file scores.
Then we can apply the formula (*) to every lrg and calculate their relevant scores to a transaction, the final step is to order the scores to get the lrg rankings.

**Validation**
One way to tune or validate this lrg rank model is to use recent data on culprit transactions. If the model gives a high ranking to the lrgs with RTI symptoms relevant to the culprit transaction, then it implies that this RTI issue could have been captured before the transaction merge if we run a recommended lrg list given based on this model. This validation method can also help us tune the model parameter λ and determine the size of the recommended lrg list.

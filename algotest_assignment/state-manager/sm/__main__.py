# Keep persistent order book in updated state
# log state changes
from multiprocessing import Process
from sm.mutations_saver import save_mutations
from sm.state_log import state_log_saver


mutation_saver_p = Process(target=save_mutations)
state_log_saver_p = Process(target=state_log_saver)

print("STARTING MUTATION AND STATE LOG SAVER")

mutation_saver_p.start()
state_log_saver_p.start()
mutation_saver_p.join()
state_log_saver_p.join()


"""CLI людини-рецензента: python3 agent/approve.py <id> <reviewer> approve|reject [коментар]"""
import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); from propose_fact import approve
if __name__ == "__main__": print(approve(sys.argv[1], sys.argv[2], sys.argv[3], " ".join(sys.argv[4:])))

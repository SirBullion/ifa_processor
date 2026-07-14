import json
from pathlib import Path

IN = Path("benchmarks/logicbench/relation_states.json")

def coord(state):
    return (state["R_A"], state["R_D"], state["T"])

def run():
    cases = json.loads(IN.read_text())

    pcm = {}
    trace = []

    rpc_exec = 0
    pcm_hits = 0
    pcm_misses = 0

    for case_id, states in enumerate(cases):
        trace.append(f"\nCASE {case_id}")

        for state in states:
            c = coord(state)

            if c in pcm:
                pcm_hits += 1
                action = "PCM_HIT_REUSE"
            else:
                pcm_misses += 1
                rpc_exec += 1
                pcm[c] = state
                action = "PCM_MISS_RPC_EXEC_STORE"

            trace.append(
                f"{action} type={state['type']} coord={c} "
                f"Y={state['Y']} R0={state['R_0']}"
            )

    total = pcm_hits + pcm_misses

    print("======================================")
    print("IFÁ PCM EXECUTION SIM")
    print("======================================")
    print(f"Cases              : {len(cases)}")
    print(f"Total state events : {total}")
    print(f"RPC executions     : {rpc_exec}")
    print(f"PCM misses         : {pcm_misses}")
    print(f"PCM hits           : {pcm_hits}")
    print(f"Unique coordinates : {len(pcm)}")
    print(f"Reuse percent      : {pcm_hits / total * 100:.2f}%")

    print("\nTRACE")
    print("-----")
    for t in trace:
        print(t)

    out = Path("benchmarks/logicbench/pcm_execution_trace.txt")
    out.write_text("\n".join(trace), encoding="utf-8")
    print(f"\nSaved: {out}")

if __name__ == "__main__":
    run()

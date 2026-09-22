import math
import random
from psyr.evaluation.metrics import ratio

def percentile(values,q):
    if not values:
        return None
    a=sorted(values); p=(len(a)-1)*q; lo=int(p); hi=math.ceil(p)
    return a[lo]+(a[hi]-a[lo])*(p-lo)

def paired_ratio_bootstrap(clusters_a,clusters_b,repetitions=2000,seed=77129):
    """Cluster maps -> (numerator, denominator). Resample same IDs in both arms."""
    if set(clusters_a) != set(clusters_b):
        raise ValueError("Unpaired cluster IDs")
    ids=sorted(clusters_a)
    def diff(sample):
        a=ratio(sum(clusters_a[i][0] for i in sample),sum(clusters_a[i][1] for i in sample))
        b=ratio(sum(clusters_b[i][0] for i in sample),sum(clusters_b[i][1] for i in sample))
        return b-a if a is not None and b is not None else None
    rng=random.Random(seed)
    draws=[diff(rng.choices(ids,k=len(ids))) for _ in range(repetitions)] if ids else []
    valid=[v for v in draws if v is not None]
    return {"difference_b_minus_a":diff(ids) if ids else None,"ci_low":percentile(valid,.025),
            "ci_high":percentile(valid,.975),"valid_bootstrap":len(valid),"undefined_bootstrap":len(draws)-len(valid),"clusters":len(ids)}

def exact_mcnemar(a,b):
    if len(a)!=len(b):
        raise ValueError("Unpaired outcomes")
    b01=sum(not x and y for x,y in zip(a,b)); b10=sum(x and not y for x,y in zip(a,b))
    n=b01+b10
    p=min(1.,2*sum(math.comb(n,k) for k in range(min(b01,b10)+1))/(2**n)) if n else 1.
    return {"b01":b01,"b10":b10,"p_exact":p,"n_pairs":len(a)}

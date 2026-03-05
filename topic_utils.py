from utils import load_aws
import pandas as pd

llm = load_aws()


def topic_preprocessing():
    df = pd.read_excel("./신규유저_매핑정의서_v0.3_20260227.xlsx",header=2)
    table_id = df['테이블 ID'][:138]
    column_id = df['컬럼 ID'][:138]
    column_name_kr = df['컬럼명'][:138]
    data_type = df['데이터 타입'][:138]
    
    
    
    
    import pdb
    pdb.set_trace()
    
    return texts
    
    
if __name__ == "__main__":

    topic_preprocessing()
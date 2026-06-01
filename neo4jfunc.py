def create_student(tx, st):
    query = f"""
        MERGE (s:Student {{name:$name,year:$year}})
    """
    tx.run(query, name=st.name, year=st.year)


def connect(tx, node1, node2):
    query = f"""
        MATCH (n:Student {{name:$name1}})
        MATCH (m:Student {{name:$name2}})
        MERGE (n)-[:CONNECTED]->(m)
        MERGE (n)<-[:CONNECTED]-(m)
    """
    tx.run(query, name1=node1.name, name2=node2.name)

import student
import random
import math
import neo4jfunc as nf
from neo4j import GraphDatabase

USER = "neo4j"
SERVER = "neo4j://localhost:7687"
PASSWORD = "awkwardfellow@detection"
driver = GraphDatabase.driver(SERVER, auth=(USER, PASSWORD))

try:
    print("Connected")
except Exception:
    print(Exception)

nbStd = int(input("Entrez le nombre d'étudiant: "))
p=math.log(nbStd)/nbStd
students = []


"""
Algorithme : Vérification et correction de la connexité du graphe
Paramètres :
  - n : nombre total d'étudiants (entier)
  - student_list : liste des étudiants

Variables locales :
  - st : étudiant courant
  - have_connection : nombre d'étudiants ayant au moins une relation
  - number_of_connection : nombre de connexions d'un étudiant donné
  - prev_student, next_student : étudiants voisins dans la liste

Début

  1. Interroger le graphe
    -> récupérer have_connection (nombre d'étudiants ayant au moins une relation)

  2. Si have_connection == n alors
       Retourner Vrai
     Fin Si

  3. Sinon
       Afficher "Graph is not connex, fixing it..."

       Pour i de 0 à n-1 faire
         st <- students[i]
         Interroger le graphe -> récupérer number_of_connection de st

         Si number_of_connection == 0 ou number_of_connection == 1 alors

           Si i != n-1 alors
             Relier st à students[i+1] (relation bidirectionnelle)
           Fin Si

           Si i != 0 alors
             Relier st à students[i-1] (relation bidirectionnelle)
           Fin Si

           Interroger le graphe -> récupérer have_connection
           Si have_connection == n alors
             Retourner Vrai
           Fin Si

         Fin Si
       Fin Pour

       Si is_connex(n, student_list) alors
         Afficher "Fixed"
         Retourner Vrai
       Fin Si

     Fin Sinon

Fin
"""


def is_connex(n, student_list):
    with driver.session(database="neo4j") as session:
        is_connex_query = f"""
            MATCH (s:Student)-[]-()
            RETURN count(DISTINCT s) AS have_connection
        """
        result = session.run(is_connex_query)
        val = result.single()
        if val["have_connection"] == n:
            return True
        else:
            print("Graph is not connex, fixing it...")
            verification_query = f"""
                MATCH (m)-[]-(s:Student {{name:$name}})
                RETURN  count(DISTINCT m) AS number_of_connection
            """
            fixing_query = f"""
                MATCH (n:Student {{name:$name}})
                MATCH (s:Student {{name:$name2}})
                MERGE (n)-[:CONNECTED]->(s)
                MERGE (n)<-[:CONNECTED]-(s)
            """
            for i in range(n):
                st = students[i]
                r = session.run(verification_query, name=st.name)
                v = r.single()
                if v["number_of_connection"] == 0 or v["number_of_connection"] == 1:
                    prev_student = None
                    next_student = None
                    if i != n - 1:
                        next_student = students[i + 1]
                        session.run(fixing_query, name=st.name, name2=next_student.name)
                    if i != 0:
                        prev_student = students[i - 1]
                        session.run(fixing_query, name=st.name, name2=prev_student.name)
                    is_connex_query = f"""
                        MATCH (s:Student)-[]-()
                        RETURN count(DISTINCT s) AS have_connection
                    """
                    result = session.run(is_connex_query)
                    val = result.single()
                    if val["have_connection"] == n:
                        return True

            if is_connex(n, student_list):
                print("Fixed")
                return True


def init(
    students, n, p=p, nb_interaction=50, limit_interaction=False
):
    with driver.session(database="neo4j") as session:
        while 1:
            session.run("MATCH (n) DETACH DELETE n")
            for i in range(n):
                st = student.Student()
                students.append(st)
                session.execute_write(nf.create_student, st)
            for n1 in students:
                if limit_interaction and nb_interaction <= n:
                    student_list = students.copy()
                    for i in range(nb_interaction):
                        n2 = random.choice(student_list)
                        connected = random.random()
                        if connected <= p and n1.name != n2.name:
                            session.execute_write(nf.connect, n1, n2)
                            student_list.remove(n2)
                else:
                    for n2 in students:
                        connected = random.random()
                        if connected >= p and n1.name != n2.name:
                            session.execute_write(nf.connect, n1, n2)
            if is_connex(nbStd, students):
                break


"""
Algorithme : Détection de toutes les cliques dans le graphe
Variables :
  - members : liste de tous les étudiants
  - adjacence : dictionnaire { étudiant -> ensemble de ses voisins }
  - cliques : liste de toutes les cliques trouvées
  - clique : clique en cours de construction
  - voisins : voisins du noeud de départ
  - is_connected_to_all : booléen
  - already_found : booléen
  - max_size : taille de la plus grande clique

Début

  1. Interroger le graphe
     -> récupérer members (liste de tous les étudiants)
     -> récupérer toutes les arêtes (a, b)

  2. Pour chaque arête (a, b) faire
       Ajouter b dans adjacence[a]
       Ajouter a dans adjacence[b]
     Fin Pour

  3. Pour chaque start dans members faire

       clique <- [start]
       voisins <- adjacence[start]

       Pour chaque candidate dans voisins faire
         is_connected_to_all <- Vrai
         Pour chaque member dans clique faire
           Si candidate ∉ adjacence[member] alors
             is_connected_to_all <- Faux
             Arrêter la boucle
           Fin Si
         Fin Pour
         Si is_connected_to_all == Vrai alors
           Ajouter candidate dans clique
         Fin Si
       Fin Pour

       already_found <- Faux
       Pour chaque c dans cliques faire
         Si set(c) == set(clique) alors
           already_found <- Vrai
           Arrêter la boucle
         Fin Si
       Fin Pour

       Si taille(clique) >= 3 ET already_found == Faux alors
         Ajouter clique dans cliques
       Fin Si

     Fin Pour

  4. Si cliques n'est pas vide alors
       max_size <- -1
       Pour chaque c dans cliques faire
         Si taille(c) > max_size alors
           max_size <- taille(c)
         Fin Si
       Fin Pour
       Afficher le nombre de cliques trouvées
       Pour i de 0 à taille(cliques)-1 faire
         clique <- cliques[i]
         Si taille(clique) == max_size alors
           marker <- " ← maximum"
         Sinon
           marker <- ""
         Fin Si
         Afficher "Clique i+1 (size taille(clique)) : clique trié + marker"
       Fin Pour
     Sinon
       Afficher "Pas de clique trouvé"
     Fin Si

  5. Retourner cliques

Fin
"""


def detect_clique():

    with driver.session(database="neo4j") as session:
        result = session.run("MATCH (n:Student) RETURN n.name AS name")
        members = [record["name"] for record in result]
        edges = session.run("""
            MATCH (n:Student)-[]-(m:Student)
            RETURN DISTINCT n.name AS a, m.name AS b
            """)
        adjacence = {m: set() for m in members}
        for record in edges:
            adjacence[record["a"]].add(record["b"])
            adjacence[record["b"]].add(record["a"])

    cliques = []

    for start in members:
        clique = [start]
        voisins = list(adjacence[start])

        for candidate in voisins:
            is_connected_to_all = True
            for member in clique:
                if candidate not in adjacence[member]:
                    is_connected_to_all = False
                    break
            if is_connected_to_all:
                clique.append(candidate)

        clique_set = set(clique)
        already_found = False
        for c in cliques:
            if set(c) == clique_set:
                already_found = True
                break

        if len(clique) >= 3 and not already_found:
            cliques.append(clique)

    if cliques:
        max_size = -1
        for c in cliques:
            if len(c) > max_size:
                max_size = len(c)

        print(f"\n{len(cliques)} clique trouvées")
        for i in range(len(cliques)):
            clique = cliques[i]
            marker = " ← maximum" if len(clique) == max_size else ""
            print(f"  Clique {i+1} (size {len(clique)}): {sorted(clique)}{marker}")
    else:
        print("Pas de clique trouvé")

    return cliques


"""
Algorithme : Inspection du graphe, détection de communautés et classification
Variables :
  - index : compteur de communautés
  - communautes : liste de toutes les communautés (liste de listes)
  - current_community : membres de la communauté courante
  - cliques : liste de toutes les cliques trouvées
  - clique_communaute : liste du nombre de cliques par communauté
  - communities : liste des communautés des membres d'une clique
  - maxClique : nombre maximum de cliques dans une communauté
  - suspect : liste des communautés suspectes
  - community_degree : liste des degrés des membres d'une communauté
  - fournisseur, dealer, consommateur : compteurs de rôles

Début

  1. Supprimer le graphe GDS 'myGraph' s'il existe

  2. Projeter le graphe en mémoire GDS
     -> Nœuds : Student
     -> Relations : CONNECTED (non dirigé)

  3. Lancer l'algorithme Louvain
     -> récupérer community_result (communautés triées par taille décroissante)

  4. index <- 0
     Pour chaque communauté r dans community_result faire
       current_community <- r["students"]
       Afficher "Communauté N° index+1"
       Afficher current_community
       Ajouter current_community dans communautes
       Pour chaque st dans current_community faire
         Étiqueter st avec community = "C{index+1}" dans Neo4j
       Fin Pour
       index <- index + 1
     Fin Pour
     Afficher "{index} communautés trouvées"

  5. Appeler detect_clique()
     -> récupérer cliques

  6. Initialiser clique_communaute à 0 pour chaque communauté
     Pour chaque clique dans cliques faire
       communities <- []
       Pour chaque person dans clique faire
         Interroger Neo4j -> récupérer la communauté de person
         Ajouter dans communities
       Fin Pour
       Si tous les éléments de communities sont identiques alors
         index <- numéro de la communauté - 1
         clique_communaute[index] <- clique_communaute[index] + 1
       Fin Si
     Fin Pour

  7. maxClique <- max(clique_communaute)
     suspect <- []
     Afficher "Nombre de clique par communauté"
     Pour i de 0 à taille(clique_communaute)-1 faire
       Afficher "Communauté i+1 : clique_communaute[i]"
       Si clique_communaute[i] == maxClique alors
         Ajouter "C{i+1}" dans suspect
       Fin Si
     Fin Pour
     Afficher "Communauté suspect : suspect"

  8. Pour chaque communauté i dans suspect faire
       index <- numéro de la communauté
       community_degree <- []
       Pour chaque person dans communautes[index] faire
         Appeler get_degree(person)
         -> Ajouter le degré dans community_degree
       Fin Pour

       fournisseur  <- nombre de degrés tels que 7 <= degree < 10
       dealer       <- nombre de degrés tels que degree >= 10
       consommateur <- nombre de degrés tels que degree < 7

       Afficher "Fournisseur : fournisseur"
       Afficher "Dealer : dealer"
       Afficher "Consommateur : consommateur"
     Fin Pour

Fin
"""


def get_degree(node):
    with driver.session(database="neo4j") as session:
        query = f"""
            MATCH (s:Student {{name:$name}})-[]-(m)
            RETURN count(DISTINCT m) as degree
        """
        result = session.run(query, name=node).single()
        return result["degree"]


def inspect():
    with driver.session(database="neo4j") as session:
        session.run("CALL gds.graph.drop('myGraph', false) YIELD graphName")
        graph_projection_query = """
            CALL gds.graph.project(
                'myGraph',
                'Student',
                {
                    CONNECTED: {
                        orientation: 'UNDIRECTED'
                    }
                }
            )
        """
        community_detection_query = """
            CALL gds.louvain.stream('myGraph')
            YIELD nodeId, communityId
            WITH gds.util.asNode(nodeId).name AS name, communityId
            RETURN communityId, collect(name) AS students, count(*) AS size
            ORDER BY size DESC    
        """
        session.run(graph_projection_query)
        community_result = session.run(community_detection_query)
        index = 0
        communautes = []
        for r in community_result:
            current_community = r["students"]
            print(f"Communauté N°{index+1}")
            print(current_community)
            communautes.append(list(current_community))
            for st in current_community:
                query = f"""
                    MATCH (s:Student {{name:$name}})
                    SET s.community = "C{index+1}"
                """
                session.run(query, name=st)
            index += 1
        print(f"\n{index} communautés trouvées.")
        cliques = detect_clique()
        clique_communaute = []
        for i in range(index):
            clique_communaute.append(0)
        for clique in cliques:
            communities = []
            for person in clique:
                query = f"""
                    MATCH (s:Student {{name:$name}})
                    RETURN s.community as community
                """
                result = session.run(query, name=person).single()
                communities.append(result["community"])
            if all(community == communities[0] for community in communities):
                index = int(communities[0][1]) - 1
                clique_communaute[index] += 1
        maxClique = max(clique_communaute)
        suspect = []

        print("\nNombre de clique par communauté")
        for i in range(len(clique_communaute)):
            print(f"Communauté {i+1}: {clique_communaute[i]}")
            if clique_communaute[i] == maxClique:
                suspect.append("C" + str(i + 1))
        print("\nCommunauté suspect:", *suspect)
        print("==================Classification=====================")
        for i in suspect:
            index = int(i[1]) - 1
            community_degree = []
            print(f"Dans Communauté C{index}")
            for person in communautes[index]:
                community_degree.append(get_degree(person))
            fournisseur = sum(
                1 for degree in community_degree if degree >= 7 and degree < 10
            )
            dealer = sum(1 for degree in community_degree if degree >= 10)
            consommateur = sum(1 for degree in community_degree if degree < 7)
            print(f"Fournisseur: {fournisseur}")
            print(f"Dealer: {dealer}")
            print(f"Consommateur: {consommateur}")
        print("======================================================")


init(students, nbStd, 0.9, 5, True)
inspect()

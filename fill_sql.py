import sys
import cPickle as pickle
import sqlite3
import codecs

build=[\
"""
CREATE TABLE IF NOT EXISTS sentence (
   sentence_id INTEGER PRIMARY KEY,
   serialized_data BLOB
);
""",
"""
CREATE TABLE IF NOT EXISTS token_index (
   token TEXT,
   sentence_id INTEGER
);
""",
"""
CREATE UNIQUE INDEX tok_sent ON token_index(token,sentence_id);
"""\
]

def get_sentences(inp):
    """
    `inp` file for reading unicode lines
    """
    curr_sent=[]
    for line in inp:
        line=line.strip()
        if not line:
            continue
        if line.startswith(u"1\t"):
            if curr_sent:
                yield curr_sent
                curr_sent=[]
        curr_sent.append(line.split(u"\t"))
   
conn=sqlite3.connect("sdata.db")

for sent_idx,sent in enumerate(get_sentences(codecs.getreader("utf-8")(sys.stdin))):
    spickle=pickle.dumps(sent,pickle.HIGHEST_PROTOCOL)
    conn.execute('INSERT OR IGNORE INTO sentence VALUES(?,?)', [sent_idx,buffer(spickle)])
    for cols in sent:
        token=cols[1]
        conn.execute('INSERT OR IGNORE INTO token_index VALUES(?,?)', [token,sent_idx])

conn.commit()

# rows=conn.execute("SELECT * FROM sentence").fetchall()
# for sid,ser in rows:
#     print sid, pickle.loads(str(ser))

conn.close()

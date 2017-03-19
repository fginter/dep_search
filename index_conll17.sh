for l in Ancient_Greek Arabic Basque Bulgarian Catalan ChineseT Croatian Czech Danish Dutch English Estonian Finnish French Galician German Greek Hebrew Hindi Hungarian Indonesian Irish Italian Japanese Kazakh Korean Latin Latvian Norwegian-Bokmaal Norwegian-Nynorsk Old_Church_Slavonic Persian Polish Portuguese Romanian Russian Slovak Slovenian Spanish Swedish Turkish Ukrainian Urdu Uyghur Vietnamese
do
    echo "***************************************************************"
    echo "Starting $l"
    date
    curl -sL https://lindat.mff.cuni.cz/repository/xmlui/bitstream/handle/11234/1-1989/$l-annotated-conll17.tar | tar xO --wildcards '*.xz' | xzcat | python build_index.py -d conll17 --lang $l --max 5000
    echo "Done $l"
    date
    echo
    echo
    echo
done


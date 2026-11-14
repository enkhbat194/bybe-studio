# BYBE Studio — Windows ашиглах заавар

## Суулгах

GitHub repository-г clone хийх эсвэл Code → Download ZIP-аар татаж задална. START_BYBE.bat дээр хоёр дарна. Python 3.11 шаардлагатай, нэмэлт Python package суулгах шаардлагагүй. Одоогийн хуучин QA V2 http://127.0.0.1:8765/ дээр нээгдэнэ.

GitHub дотор аудио, видео, QA хувийн мэдээллийг зориуд оруулаагүй. Нэгдсэн ажлын хавтас локал компьютертээ хэвээр байна.

Хэрэв V2-ийн байрлал өөр бол репогийн үндсэн хавтаст local-config.json файл үүсгэнэ (GitHub-д орохгүй):

    {"legacy_workspace":"D:\\Czech800\\Czech800_QA_STUDIO_V2_CHROME_EDITOR\\Czech800_QA_STUDIO_V2"}

## Хуучин сайтын төлөв ба засварын файлууд

    py -3.11 scripts\bybe.py status

JSON дээр edited гэж байгаад бодит edits/*.wav байхгүй бол WARN гарна. Хоосон эсвэл хуурамч backup үүсгэхгүй.

## Нэг ZIP бүрэн нөөцлөлт

    py -3.11 scripts\bybe.py backup

local_data/backups дотор QA JSON + qa_records.json + edits дахь бодит засварласан WAV + хувилбарын түүх + SHA256 бүртгэл орно. Том эх MKV-ийг дахин хуулбарлахгүй.

## Эх бичлэгийн холболт

Файлын замыг бодитоор зөв бич; доорх 003.mkv, 004.mkv, 005.mkv нь зөвхөн жишээ:

    py -3.11 scripts\bybe.py link-source --part 003 --file "D:\Czech800\raw\003.mkv"
    py -3.11 scripts\bybe.py link-source --part 004 --file "D:\Czech800\raw\004.mkv"
    py -3.11 scripts\bybe.py link-source --part 005 --file "D:\Czech800\raw\005.mkv"

Бүртгэхдээ файл хаана байгааг шалгаж, SHA256 хэш хадгална. local_data/source_map.json-ийг GitHub-д хуулахгүй.

## V3 туршилтын waveform редактор

Эх видеонуудыг link-source командаар бүртгэсний дараа START_BYBE_V3_PILOT.bat дээр хоёр дарна. Шинэ сайт http://127.0.0.1:8766/ нээгдэнэ. FFmpeg-ийг PATH-д тохируулсан байх хэрэгтэй.

Үг сонго → 'Эх видеоны контекстийг ачаалах' → долгионы эхлэл/төгсгөлийг чирэх → сонгосон хэсгийг сонсох → шинэ WAV кандидат хадгалах → 6 шалгалтын нүдийг тэмдэглэх → батлах.

Энэ сайт хуучин V2-г өөрчлөхгүй. Шинэ WAV local_data/revisions/ дотор тусдаа хадгалагдана. Нэг ZIP backup товчтой. V3 туршилтын кодыг бодит Windows дээр бүрэн QA баталгаажуулсан гэж үзэхгүй.

## Энэ release-д БАЙХГҮЙ

V3 waveform pilot бий болсон, харин бүрэн Source Manager GUI, SQLite, бие даасан MCP, OCR/ASR, Google Drive автомат upload хараахан байхгүй. Эдгээрийг ажиллаж байгаа мэт тайлагнахгүй. Эдгээрийг суурь аюулгүй болсны дараа нэмнэ.

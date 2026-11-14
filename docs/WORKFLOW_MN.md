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

## Энэ release-д БАЙХГҮЙ

Одоохондоо шинэ V3 waveform, автомат эх файлтай зааг тааруулах, MCP, OCR/ASR, Google Drive автоматаар upload хийх боломжийг ажиллаж байгаа гэж үзэж болохгүй. Эдгээрийг суурь аюулгүй болсны дараа нэмнэ.

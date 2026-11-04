import 'dart:io';

Future<void> saveAndDownloadFile(String fileName, String content) async {
  final Directory dir = Directory.systemTemp;
  final File file = File('${dir.path}/$fileName');
  await file.writeAsString(content);
}

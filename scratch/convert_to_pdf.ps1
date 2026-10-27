$docxPath = "C:\Users\achyu\Desktop\BDA\output\Weather_Data_Storage_and_Analysis_MongoDB_Report.docx"
$pdfPath = "C:\Users\achyu\Desktop\BDA\output\Weather_Data_Storage_and_Analysis_MongoDB_Report.pdf"

$word = New-Object -ComObject Word.Application
$word.Visible = $false
try {
    $doc = $word.Documents.Open($docxPath, $false, $true) # ReadOnly = True
    $pages = $doc.ComputeStatistics(2)
    Write-Host "Opened DOCX successfully! Page count: $pages"
    # 17 = wdExportFormatPDF
    $doc.ExportAsFixedFormat($pdfPath, 17)
    $doc.Close([ref]0) # wdDoNotSaveChanges
    Write-Host "Exported PDF successfully to: $pdfPath"
} catch {
    Write-Host "COM Error: $_"
} finally {
    $word.Quit()
}

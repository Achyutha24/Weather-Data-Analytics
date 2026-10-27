$ErrorActionPreference = 'Stop'
$reportPath = 'C:\Users\achyu\Desktop\BDA\output\Weather_Data_Storage_and_Analysis_MongoDB_Report.docx'
$previewPath = 'C:\Users\achyu\Desktop\BDA\scratch\draft-review-1.pdf'
$word = New-Object -ComObject Word.Application
$word.Visible = $false
$word.DisplayAlerts = 0
$doc = $word.Documents.Open($reportPath, $false, $false)
try {
    foreach ($sectionNumber in @(5, 12)) {
        $section = $doc.Sections.Item($sectionNumber)
        $header = $section.Headers.Item(1)
        $footer = $section.Footers.Item(1)

        foreach ($spec in @(
            @{ Collection = $header.Shapes; Anchor = $header.Range; Prefix = 'WeatherHeaderRule'; X1 = 56; Y = 48; X2 = 539; FirstColor = 163 + 84 * 256 + 18 * 65536; SecondColor = 208 + 120 * 256 + 42 * 65536 },
            @{ Collection = $footer.Shapes; Anchor = $footer.Range; Prefix = 'WeatherFooterRule'; X1 = 56; Y = 776; X2 = 539; FirstColor = 163 + 84 * 256 + 18 * 65536; SecondColor = 208 + 120 * 256 + 42 * 65536 }
        )) {
            $shapes = $spec.Collection
            for ($i = $shapes.Count; $i -ge 1; $i--) {
                $old = $shapes.Item($i)
                if ($old.Name -like ($spec.Prefix + '*')) { $old.Delete() }
            }
            foreach ($offset in @(0, 2.5)) {
                $shape = $shapes.AddLine([single]$spec.X1, [single]($spec.Y + $offset), [single]$spec.X2, [single]($spec.Y + $offset), $spec.Anchor)
                $shape.Name = $spec.Prefix + [string]($offset -eq 0 ? 'Dark' : 'Accent')
                $shape.RelativeHorizontalPosition = 1
                $shape.RelativeVerticalPosition = 1
                $shape.Left = [single]$spec.X1
                $shape.Top = [single]($spec.Y + $offset)
                $shape.WrapFormat.Type = 3
                $shape.LockAnchor = $true
                $shape.Line.Visible = -1
                $shape.Line.ForeColor.RGB = if ($offset -eq 0) { $spec.FirstColor } else { $spec.SecondColor }
                $shape.Line.Weight = [single]0.8
            }
        }
    }

    $doc.Repaginate()
    $doc.Fields.Update() | Out-Null
    foreach ($section in $doc.Sections) {
        foreach ($footer in $section.Footers) { $footer.Range.Fields.Update() | Out-Null }
    }
    $pages = $doc.ComputeStatistics(2)
    $doc.ExportAsFixedFormat($previewPath, 17)
    $doc.Save()
    Write-Output "pages=$pages"
}
finally {
    $doc.Close()
    $word.Quit()
}

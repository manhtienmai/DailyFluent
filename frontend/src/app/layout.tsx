import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "DailyFluent",
  description: "Nền tảng học ngôn ngữ hiệu quả",
  icons: { icon: "/logo_official.png" },
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="vi" suppressHydrationWarning>
      <head>
        <link
          href="https://fonts.googleapis.com/css2?family=Be+Vietnam+Pro:wght@300;400;500;600;700&family=Noto+Sans+JP:wght@300;400;500;700&family=Noto+Serif+JP:wght@400;500;700&family=Zen+Maru+Gothic:wght@400;500;700&family=Kosugi+Maru&family=Sawarabi+Mincho&family=M+PLUS+Rounded+1c:wght@400;500;700&display=swap"
          rel="stylesheet"
        />
      </head>
      <body>
        <script dangerouslySetInnerHTML={{ __html: `
          (function(){
            var m={"noto-sans":"'Noto Sans JP'","noto-serif":"'Noto Serif JP'","zen-maru":"'Zen Maru Gothic'","kosugi-maru":"'Kosugi Maru'","sawarabi":"'Sawarabi Mincho'","mplus-rounded":"'M PLUS Rounded 1c'"};
            var f=localStorage.getItem("df-jp-font");
            if(f&&m[f])document.documentElement.style.setProperty("--font-jp-user",m[f]);
          })();
        `}} />
        {children}
      </body>
    </html>
  );
}

Add-Type -AssemblyName System.Drawing
Add-Type -ReferencedAssemblies System.Drawing.Common -TypeDefinition @'
using System; using System.Drawing; using System.Drawing.Drawing2D;
public class FaceBlend {
public static void Run(string src,string edit,string dest){
using(var b=new Bitmap(src)) using(var e=new Bitmap(edit)) {
float s=b.Width/1400f; int x=(int)(605*s),y=(int)(65*s),w=(int)(180*s),h=(int)(190*s);
using(var patch=new Bitmap(w,h)) using(var g=Graphics.FromImage(patch)) {
g.DrawImage(e,0,0,w,h);
PointF[] p={new PointF(175,240),new PointF(230,225),new PointF(330,240),new PointF(420,205),new PointF(490,225),new PointF(515,300),new PointF(495,415),new PointF(435,500),new PointF(350,550),new PointF(280,540),new PointF(220,475),new PointF(185,400),new PointF(165,310)};
using(var path=new GraphicsPath()){path.AddPolygon(p);
for(int j=0;j<h;j++)for(int i=0;i<w;i++){float u=i*720f/w,v=j*760f/h;if(!path.IsVisible(u,v))continue;double d=10000;
for(int k=0;k<p.Length;k++){var a=p[k];var z=p[(k+1)%p.Length];double dx=z.X-a.X,dy=z.Y-a.Y,t=Math.Max(0,Math.Min(1,((u-a.X)*dx+(v-a.Y)*dy)/(dx*dx+dy*dy)));d=Math.Min(d,Math.Sqrt(Math.Pow(u-a.X-t*dx,2)+Math.Pow(v-a.Y-t*dy,2)));}
double alpha=Math.Min(1,d/15);var c=b.GetPixel(x+i,y+j);var n=patch.GetPixel(i,j);b.SetPixel(x+i,y+j,Color.FromArgb(c.A,(int)(c.R*(1-alpha)+n.R*alpha),(int)(c.G*(1-alpha)+n.G*alpha),(int)(c.B*(1-alpha)+n.B*alpha)));
}} b.Save(dest,System.Drawing.Imaging.ImageFormat.Png);
}}
}}
'@
[FaceBlend]::Run('C:\Users\Admin\Dropbox\YTMF\Amara_2026\Press_On\Clip_Package_v2\02_VERSE1\seg17_vestibule_performance\reference_candidates\hf_20260917_114555_23642300-7038-4f21-b226-14cbd3e0da18.png','C:\Users\Admin\.codex\generated_images\01a08fc7-2484-7c62-813b-c127140ea78d\exec-0b24075b-9406-4fb7-9dcf-b38610de3200.png','D:\App development\YouTube_Movie_Factory_v3\candidate_2_masked_face_v1.png')

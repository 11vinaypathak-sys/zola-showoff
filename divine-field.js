import * as THREE from 'three';

// Analytic light: no image downloads, shadow maps, ray marching or simulation buffers.
export function createDivineField(scene, regions, reduced) {
  const clock={value:0}, auras=[];
  const vertex=`varying vec2 vUv; void main(){vUv=uv;gl_Position=projectionMatrix*modelViewMatrix*vec4(position,1.);}`;
  const fragment=`varying vec2 vUv; uniform vec3 hue; uniform float time,kind,attention;
  float ring(float r,float at,float width){return exp(-pow((r-at)/max(width,fwidth(r)*.7),2.));}
  void main(){vec2 p=(vUv-.5)*2.;float r=length(p);if(r>1.)discard;float a=atan(p.y,p.x);
    float phase=time*.12+kind*.72;
    float petals=kind<.5?6.:kind<1.5?3.:kind<2.5?8.:kind<3.5?12.:6.;
    float wave=.025*sin(a*petals+phase)*sin(a*3.-phase*.6);
    float rim=ring(r,.66+wave,.005)+ring(r,.72+wave*.5,.0025)*.45;
    float outer=ring(r,.88,.0018)*(.2+.8*pow(.5+.5*cos(a*60.),12.));
    float arch=ring(r,.49+.11*cos(a*petals+phase*.32),.003)*.44;
    float rays=pow(max(0.,cos(a*(petals*3.)+phase*.14)),40.)*exp(-pow((r-.71)/.14,2.))*.14;
    float veil=exp(-pow((r-.62)/.15,2.))*.045;
    float center=exp(-r*r*12.)*.024;
    float power=(rim*.34+outer*.22+arch+rays+veil+center)*attention;
    gl_FragColor=vec4(mix(hue,vec3(1.,.91,.74),.18)*power,1.);
  }`;
  const plane=new THREE.PlaneGeometry(1,1);
  const shellGeo=new THREE.SphereGeometry(1,32,20);
  regions.concat([{c:new THREE.Vector3(),hex:0xe6dca5}]).forEach((g,i)=>{
    const uniforms={hue:{value:new THREE.Color(g.hex)},time:clock,kind:{value:i},attention:{value:1}};
    const mat=new THREE.ShaderMaterial({uniforms,vertexShader:vertex,fragmentShader:fragment,transparent:true,blending:THREE.AdditiveBlending,depthWrite:false,fog:false,toneMapped:false});
    const halo=new THREE.Mesh(plane,mat);halo.position.copy(g.c);const sizes=[[15,15],[13,19],[17,14],[18,12],[14,18],[13,13]][i];halo.scale.set(sizes[0],sizes[1],1);halo.renderOrder=1;scene.add(halo);
    const shell=new THREE.Mesh(shellGeo,new THREE.ShaderMaterial({uniforms,
      vertexShader:`varying vec3 vN,vV,vP;void main(){vP=position;vec4 mv=modelViewMatrix*vec4(position,1.);vN=normalize(normalMatrix*normal);vV=normalize(-mv.xyz);gl_Position=projectionMatrix*mv;}`,
      fragmentShader:`varying vec3 vN,vV,vP;uniform vec3 hue;uniform float time,kind,attention;
      void main(){float rim=pow(1.-abs(dot(normalize(vN),normalize(vV))),3.5);
      float latitude=sin(vP.y*22.+time*.16+kind);float bands=pow(max(0.,latitude),18.);
      float wisps=.5+.5*sin(atan(vP.z,vP.x)*9.+vP.y*8.-time*.13);
      float light=rim*(.025+.05*wisps)+bands*.014*rim;
      gl_FragColor=vec4(hue*light*attention,1.);}`,
      transparent:true,blending:THREE.AdditiveBlending,depthWrite:false,side:THREE.FrontSide,fog:false,toneMapped:false}));
    shell.position.copy(g.c);shell.scale.setScalar(i===5?4.4:5.3);scene.add(shell);const shapes=[[1,.85,1],[.8,1.25,.8],[1.12,.85,1],[1.15,.68,1.15],[.88,1.18,.88],[1,1,1]][i];shell.scale.multiply(new THREE.Vector3(...shapes));const tilt=new THREE.Quaternion().setFromEuler(new THREE.Euler([.15,-.2,.24,-.3,.14,0][i],[.2,-.12,.1,.22,-.24,0][i],[.08,-.12,.17,.2,-.1,0][i]));auras.push({halo,shell,uniforms,tilt});
  });
  // A low, open celestial compass gives the scattered worlds one shared plane.
  const compass=new THREE.Mesh(new THREE.PlaneGeometry(100,100),new THREE.ShaderMaterial({
    uniforms:{time:clock,strength:{value:.7}},vertexShader:vertex,
    fragmentShader:`varying vec2 vUv;uniform float time,strength;
    float ring(float r,float n){return exp(-pow((r-n)/.0007,2.));}
    void main(){vec2 p=vUv-.5;float r=length(p);if(r>.49||r<.06)discard;float a=atan(p.y,p.x);
    float circles=ring(r,.105)*.4+ring(r,.24)*.26+ring(r,.39)*.4+ring(r,.405)*.14;
    float ticks=pow(max(0.,cos(a*120.)),50.)*exp(-pow((r-.392)/.007,2.))*.3;
    float spokes=pow(max(0.,cos(a*10.)),250.)*smoothstep(.10,.15,r)*smoothstep(.40,.34,r)*.075;
    gl_FragColor=vec4(vec3(.63,.53,.34)*(circles+ticks+spokes)*strength,1.);}`,
    transparent:true,blending:THREE.AdditiveBlending,depthWrite:false,side:THREE.DoubleSide,fog:false,toneMapped:false}));
  compass.rotation.x=-Math.PI/2;compass.position.y=-10;scene.add(compass);
  // One draw call for all orbiting light grains, motion entirely on the GPU.
  const positions=[],origins=[],colors=[],phases=[];
  for(let j=0;j<regions.length;j++)for(let k=0;k<92;k++){
    const a=k*2.3999632297+j,r=4.5+(k%19)/19*3.6,y=Math.sin(k*1.79)*2.8;
    positions.push(Math.cos(a)*r,y,Math.sin(a)*r);origins.push(...regions[j].c.toArray());
    const c=new THREE.Color(regions[j].hex).lerp(new THREE.Color(0xffe8bb),.3);colors.push(c.r,c.g,c.b);phases.push(k*.71+j);
  }
  const geo=new THREE.BufferGeometry();geo.setAttribute('position',new THREE.Float32BufferAttribute(positions,3));geo.setAttribute('origin',new THREE.Float32BufferAttribute(origins,3));geo.setAttribute('color',new THREE.Float32BufferAttribute(colors,3));geo.setAttribute('phase',new THREE.Float32BufferAttribute(phases,1));
  const motes=new THREE.Points(geo,new THREE.ShaderMaterial({uniforms:{time:clock},vertexColors:true,
    vertexShader:`attribute vec3 origin;attribute float phase;uniform float time;varying vec3 vC;varying float glow;
    void main(){float a=time*.045;vec3 p=position;p.xz=mat2(cos(a),-sin(a),sin(a),cos(a))*p.xz;p.y+=sin(time*.24+phase)*.25;vec4 mv=modelViewMatrix*vec4(origin+p,1.);gl_Position=projectionMatrix*mv;gl_PointSize=clamp(80./-mv.z,1.,4.);vC=color;glow=.22+.36*pow(.5+.5*sin(time*.5+phase),3.);}`,
    fragmentShader:`varying vec3 vC;varying float glow;void main(){float d=length(gl_PointCoord-.5)*2.;if(d>1.)discard;gl_FragColor=vec4(vC*pow(1.-d,2.)*glow,1.);}`,
    transparent:true,blending:THREE.AdditiveBlending,depthWrite:false,fog:false,toneMapped:false}));motes.frustumCulled=false;scene.add(motes);
  return {auras,compass,motes,update(t,camera,current,hover){clock.value=reduced?0:t;compass.material.uniforms.strength.value=current<0?.65:.12;auras.forEach((a,i)=>{a.halo.quaternion.copy(camera.quaternion).multiply(a.tilt);const target=i===current?1:i===hover?1.1:current<0?.8:.16;a.uniforms.attention.value+=(target-a.uniforms.attention.value)*.06;});}};
}

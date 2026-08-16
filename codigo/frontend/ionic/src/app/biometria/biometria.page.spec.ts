import { ComponentFixture, TestBed } from '@angular/core/testing';
import { HttpClientTestingModule } from '@angular/common/http/testing';
import { RouterTestingModule } from '@angular/router/testing';
import { IonicModule } from '@ionic/angular';

import { BiometriaPage } from './biometria.page';
import { SharedModule } from '../shared/shared.module';

describe('BiometriaPage', () => {
  let component: BiometriaPage;
  let fixture: ComponentFixture<BiometriaPage>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      declarations: [BiometriaPage],
      imports: [IonicModule.forRoot(), HttpClientTestingModule, RouterTestingModule, SharedModule],
    }).compileComponents();

    fixture = TestBed.createComponent(BiometriaPage);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
